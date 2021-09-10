import re
from datetime import date

import filetype
from applications.api.v1.status_transition_validator import (
    ApplicationBatchStatusValidator,
    ApplicationStatusValidator,
)
from applications.enums import (
    ApplicationBatchStatus,
    ApplicationStatus,
    AttachmentRequirement,
    AttachmentType,
    BenefitType,
    OrganizationType,
)
from applications.models import (
    Application,
    ApplicationBasis,
    ApplicationBatch,
    ApplicationLogEntry,
    Attachment,
    DeMinimisAid,
    Employee,
)
from common.exceptions import BenefitAPIException
from common.utils import PhoneNumberField, xgroup
from companies.api.v1.serializers import CompanySerializer
from companies.models import Company
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.forms import ImageField, ValidationError as DjangoFormsValidationError
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from helsinkibenefit.settings import MAX_UPLOAD_SIZE, MINIMUM_WORKING_HOURS_PER_WEEK
from rest_framework import serializers


class ApplicationBasisSerializer(serializers.ModelSerializer):
    """
    Only the unique identifier is exposed through the API.
    """

    class Meta:
        model = ApplicationBasis
        fields = [
            "identifier",
        ]
        extra_kwargs = {
            "identifier": {
                "help_text": "Unique slug that identifies the basis",
            }
        }


class AttachmentSerializer(serializers.ModelSerializer):
    # this limit is a security feature, not a business rule
    MAX_ATTACHMENTS_PER_APPLICATION = 20

    class Meta:
        model = Attachment
        fields = [
            "id",
            "application",
            "attachment_type",
            "attachment_file",
            "attachment_file_name",
            "content_type",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    attachment_file_name = serializers.SerializerMethodField(
        "get_attachment_file_name",
        help_text="The name of the uploaded file",
    )

    def get_attachment_file_name(self, obj):
        return obj.attachment_file.name

    ATTACHMENT_MODIFICATION_ALLOWED_STATUSES = (
        ApplicationStatus.ADDITIONAL_INFORMATION_NEEDED,
        ApplicationStatus.DRAFT,
    )

    def validate(self, data):
        """
        Validation includes:
        * validate that adding attachments is allowed in this application status
        * rudimentary validation of file content to guard against accidentally uploading
        invalid files.
        """
        if (
            data["application"].status
            not in self.ATTACHMENT_MODIFICATION_ALLOWED_STATUSES
        ):
            raise serializers.ValidationError(
                _("Can not add attachment to an application in this state")
            )

        if data["attachment_file"].size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                format_lazy(
                    _("Upload file size cannot be greater than {size} bytes"),
                    size=MAX_UPLOAD_SIZE,
                )
            )

        if (
            len(data["application"].attachments.all())
            >= self.MAX_ATTACHMENTS_PER_APPLICATION
        ):
            raise serializers.ValidationError(_("Too many attachments"))
        if data["content_type"] == "application/pdf":
            if not self._is_valid_pdf(data["attachment_file"]):
                raise serializers.ValidationError(_("Not a valid pdf file"))
        elif not self._is_valid_image(data["attachment_file"]):
            # only pdf and image files are listed in ATTACHMENT_CONTENT_TYPE_CHOICES, so if we get here,
            # the content type is an image file
            raise serializers.ValidationError(_("Not a valid image file"))
        return data

    def _is_valid_image(self, uploaded_file):
        try:
            im = ImageField()
            # check if the file is a valid image
            im.to_python(uploaded_file)
        except DjangoFormsValidationError:
            return False
        else:
            return True

    def _is_valid_pdf(self, uploaded_file):
        file_pos = uploaded_file.tell()
        mime_type = None
        if file_type_guess := filetype.guess(uploaded_file):
            mime_type = file_type_guess.mime
        uploaded_file.seek(file_pos)  # restore position
        return mime_type == "application/pdf"


class DeMinimisAidSerializer(serializers.ModelSerializer):
    """
    De minimis aid objects are meant to be edited together with their Application object.
    The "ordering" field is not editable and is ignored if present in POST/PUT data.
    The ordering of the DeMinimisAid objects is determined by their order in the "de_minimis_aid_set" list
    in the Application.
    """

    MAX_AID_AMOUNT = 200000
    amount = serializers.DecimalField(
        max_digits=DeMinimisAid.amount.field.max_digits,
        decimal_places=DeMinimisAid.amount.field.decimal_places,
        min_value=1,
        max_value=MAX_AID_AMOUNT,
        help_text="see MAX_AMOUNT",
    )

    def validate_granted_at(self, value):
        min_date = date(date.today().year - 4, 1, 1)
        if value < min_date:
            raise serializers.ValidationError(_("Grant date too much in past"))
        elif value > date.today():
            raise serializers.ValidationError(_("Grant date can not be in the future"))
        return value

    class Meta:
        model = DeMinimisAid
        fields = [
            "id",
            "granter",
            "granted_at",
            "amount",
            "ordering",
        ]
        read_only_fields = [
            "ordering",
        ]
        extra_kwargs = {
            "granter": {
                "help_text": "Granter of the benefit",
            },
            "granted_at": {
                "help_text": "Date max. four years into past",
            },
            "ordering": {
                "help_text": "Note: read-only field, ignored on input",
            },
        }


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Employee objects are meant to be edited together with their Application object.
    """

    SSN_REGEX = r"^(\d{6})[aA+-](\d{3})([0-9A-FHJ-NPR-Ya-fhj-npr-y])$"

    SSN_CHEKSUM = {
        int(k): v
        for k, v in xgroup(
            (
                "0    0    16    H "
                "1    1    17    J "
                "2    2    18    K "
                "3    3    19    L "
                "4    4    20    M "
                "5    5    21    N "
                "6    6    22    P "
                "7    7    23    R "
                "8    8    24    S "
                "9    9    25    T "
                "10    A    26    U "
                "11    B    27    V "
                "12    C    28    W "
                "13    D    29    X "
                "14    E    30    Y "
                "15    F"
            ).split()
        )
    }

    phone_number = PhoneNumberField(
        allow_blank=True,
        help_text="Employee phone number normalized (start with zero, without country code)",
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "first_name",
            "last_name",
            "social_security_number",
            "phone_number",
            "email",
            "employee_language",
            "job_title",
            "monthly_pay",
            "vacation_money",
            "other_expenses",
            "working_hours",
            "collective_bargaining_agreement",
            "is_living_in_helsinki",
            "commission_amount",
            "commission_description",
            "created_at",
        ]
        read_only_fields = [
            "ordering",
        ]

    def validate_social_security_number(self, value):
        """
        For more info about the checksum validation, see "Miten henkilötunnukset tarkistusmerkki lasketaan?" in
        https://dvv.fi/henkilotunnus
        """
        if value == "":
            return value

        m = re.match(self.SSN_REGEX, value)
        if not m:
            raise serializers.ValidationError(_("Social security number invalid"))

        expect_checksum = EmployeeSerializer.SSN_CHEKSUM[
            int((m.group(1) + m.group(2)).lstrip("0")) % 31
        ].lower()
        if expect_checksum != m.group(3).lower():
            raise serializers.ValidationError(
                _("Social security number checksum invalid")
            )

        return value

    def validate_working_hours(self, value):
        if value and value < MINIMUM_WORKING_HOURS_PER_WEEK:
            raise serializers.ValidationError(
                format_lazy(
                    _("Working hour must be greater than {min_hour} per week"),
                    min_hour=MINIMUM_WORKING_HOURS_PER_WEEK,
                )
            )
        return value

    def validate_monthly_pay(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("Monthly pay must be greater than 0"))

    def validate_vacation_money(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                _("Vacation money must be a positive number")
            )

    def validate_other_expenses(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                _("Other expenses must be a positive number")
            )


class ApplicationBatchSerializer(serializers.ModelSerializer):
    """
    Grouping of applications for batch processing.
    One Application can belong to at most one ApplicationBatch at a time.
    """

    status = serializers.ChoiceField(
        choices=ApplicationBatchStatus.choices,
        validators=[ApplicationBatchStatusValidator()],
        help_text="Status of the application, visible to the applicant",
    )

    applications = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=False,
        queryset=Application.objects.all(),
        help_text="Applications in this batch (read-only)",
    )

    proposal_for_decision = serializers.ChoiceField(
        choices=[ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED],
        help_text="Proposed decision for Ahjo",
    )

    class Meta:
        model = ApplicationBatch
        fields = [
            "id",
            "status",
            "applications",
            "proposal_for_decision",
            "decision_maker_title",
            "decision_maker_name",
            "section_of_the_law",
            "decision_date",
            "expert_inspector_name",
            "expert_inspector_email",
            "created_at",
        ]
        read_only_fields = [
            "created_at",
        ]
        extra_kwargs = {
            "decision_maker_title": {
                "help_text": "Title of the decision maker in Ahjo",
            },
            "decision_maker_name": {
                "help_text": "Nameof the decision maker in Ahjo",
            },
            "section_of_the_law": {
                "help_text": "Section of the law that the Ahjo decision is based on",
            },
            "decision_date": {
                "help_text": "Date of decision in Ahjo",
            },
            "expert_inspector_name": {
                "help_text": "The name of application handler at the city of Helsinki (for Talpa)",
            },
            "expert_inspector_email": {
                "help_text": "The email of application handler at the city of Helsinki (for Talpa)",
            },
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        applications = validated_data.pop("applications", None)
        application_batch = super().update(instance, validated_data)
        if applications is not None:
            self._update_applications(application_batch, applications)
        return application_batch

    @transaction.atomic
    def create(self, validated_data):
        applications = validated_data.pop("applications", None)
        application_batch = super().create(validated_data)
        if applications is not None:
            self._update_applications(application_batch, applications)
        return application_batch

    def _update_applications(self, application_batch, applications):
        if {application.pk for application in application_batch.applications.all()} != {
            application.pk for application in applications
        }:
            if not application_batch.applications_can_be_modified:
                raise serializers.ValidationError(
                    {
                        "applications": _(
                            "Applications in a batch can not be changed when batch is in this status"
                        )
                    }
                )

            for application in applications:
                if str(application.status) != str(
                    application_batch.proposal_for_decision
                ):
                    raise serializers.ValidationError(
                        {
                            "applications": _(
                                "This application has invalid status and can not be added to this batch"
                            )
                        }
                    )

        application_batch.applications.set(applications)


class ApplicationSerializer(serializers.ModelSerializer):

    """
    Fields in the Company model come from YTJ/other source and are not editable by user, and are listed
    in read_only_fields. If sent in the request, these fields are ignored.
    """

    status = serializers.ChoiceField(
        choices=ApplicationStatus.choices,
        validators=[ApplicationStatusValidator()],
        help_text="Status of the application, visible to the applicant",
    )

    employee = EmployeeSerializer()

    company = CompanySerializer(read_only=True)

    attachments = AttachmentSerializer(
        read_only=True,
        many=True,
        help_text="Attachments of the application (read-only)",
    )

    bases = serializers.SlugRelatedField(
        many=True,
        slug_field="identifier",
        queryset=ApplicationBasis.objects.filter(is_active=True),
        help_text="List of application basis identifiers",
    )

    de_minimis_aid_set = DeMinimisAidSerializer(
        many=True,
        help_text="List of de minimis aid associated with this application."
        "Total amount must be less than MAX_AID_AMOUNT",
    )

    batch = ApplicationBatchSerializer(
        read_only=True, help_text="Application batch of this application, if any"
    )

    create_application_for_company = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        queryset=Company.objects.all(),
        help_text=(
            "To be used when a logged-in application handler creates a new application based on a paper application"
            "received via mail. Ordinary applicants can only create applications for their own company."
        ),
    )

    class Meta:
        model = Application
        fields = [
            "id",
            "status",
            "employee",
            "batch",
            "company",
            "company_name",
            "company_form",
            "organization_type",
            "submitted_at",
            "bases",
            "available_bases",
            "attachment_requirements",
            "available_benefit_types",
            "official_company_street_address",
            "official_company_city",
            "official_company_postcode",
            "use_alternative_address",
            "alternative_company_street_address",
            "alternative_company_city",
            "alternative_company_postcode",
            "company_department",
            "company_bank_account_number",
            "company_contact_person_first_name",
            "company_contact_person_last_name",
            "company_contact_person_phone_number",
            "company_contact_person_email",
            "association_has_business_activities",
            "applicant_language",
            "co_operation_negotiations",
            "co_operation_negotiations_description",
            "pay_subsidy_granted",
            "pay_subsidy_percent",
            "additional_pay_subsidy_percent",
            "apprenticeship_program",
            "archived",
            "application_step",
            "benefit_type",
            "start_date",
            "end_date",
            "de_minimis_aid",
            "de_minimis_aid_set",
            "create_application_for_company",
            "last_modified_at",
            "created_at",
            "attachments",
            "ahjo_decision",
        ]
        read_only_fields = [
            "submitted_at",
            "application_number",
            "available_bases",
            "attachment_requirements",
            "company_name",
            "company_form",
            "official_company_street_address",
            "official_company_city",
            "official_company_postcode",
            "available_benefit_types",
            "last_modified_at",
            "created_at",
        ]
        extra_kwargs = {
            "company_name": {
                "help_text": "The application should retain the Company name, as it was at the time the"
                " application was created, to maintain historical accuracy.",
            },
            "company_form": {
                "help_text": "Company city from official sources (YTJ) at the time the application was created",
            },
            "official_company_street_address": {
                "help_text": "Company street address from official sources (YTJ/other) at"
                "the time the application was created",
            },
            "official_company_city": {
                "help_text": "Company city from official sources (YTJ/other) at"
                "the time the application was created",
            },
            "official_company_postcode": {
                "help_text": "Company post code from official sources (YTJ/other) at"
                "the time the application was created",
            },
            "use_alternative_address": {
                "help_text": "The user has an option of using an alternative address."
                "This will then be used instead of the address fetched from YTJ/PRH.",
            },
            "alternative_company_street_address": {
                "help_text": "User-supplied address, to be used in Helsinki Benefit related issues",
            },
            "alternative_company_city": {
                "help_text": "User-supplied city, to be used in Helsinki Benefit related issues",
            },
            "alternative_company_postcode": {
                "help_text": "User-supplied postcode, to be used in Helsinki Benefit related issues",
            },
            "company_department": {
                "help_text": "Company department address",
            },
            "company_bank_account_number": {
                "help_text": "IBAN formatted bank account number",
            },
            "company_contact_person_first_name": {
                "help_text": "First name of the contact person",
            },
            "company_contact_person_last_name": {
                "help_text": "Last name of the contact person",
            },
            "company_contact_person_phone_number": {
                "help_text": "Phone number of the contact person, must a Finnish phone number",
            },
            "company_contact_person_email": {
                "help_text": "Email address of the contact person",
            },
            "association_has_business_activities": {
                "help_text": "field is visible and yes/no answer is required/allowed"
                "only if applicant is an association",
            },
            "applicant_language": {
                "help_text": "Language to be used when contacting the contact person",
            },
            "co_operation_negotiations": {
                "help_text": "If set to True, then the negotiations description must be filled",
            },
            "co_operation_negotiations_description": {
                "help_text": "Free text entered by the applicant",
            },
            "pay_subsidy_granted": {
                "help_text": "Is pay subsidy granted for the employment?",
            },
            "pay_subsidy_percent": {
                "help_text": "Percentage of the pay subsidy granted",
            },
            "additional_pay_subsidy_percent": {
                "help_text": "Percentage of the pay subsidy granted (If there is another pay subsidy grant)",
            },
            "apprenticeship_program": {
                "help_text": "Is the employee in apprenticeship program?",
            },
            "archived": {
                "help_text": "Flag indicating the application is archived and should not usually be shown to the user",
            },
            "benefit_type": {
                "help_text": "Benefit type of this application",
            },
            "application_step": {
                "help_text": "current/latest application step shown in the UI",
            },
            "start_date": {
                "help_text": "Must be within the current year.",
            },
            "end_date": {
                "help_text": "Must be after the start date.",
            },
            "de_minimis_aid": {
                "help_text": "Null indicates user has no yet made the selection",
            },
            "ahjo_decision": {
                "help_text": "Decision made in Ahjo, if any",
            },
        }

    ahjo_decision = serializers.ReadOnlyField()

    submitted_at = serializers.SerializerMethodField("get_submitted_at")

    last_modified_at = serializers.SerializerMethodField(
        "get_last_modified_at",
        help_text="Last modified timestamp. Only handlers see the timestamp of non-draft applications.",
    )

    organization_type = serializers.SerializerMethodField(
        "get_organization_type",
        help_text="The general type of the applicant organization",
    )

    available_bases = serializers.SerializerMethodField(
        "get_available_bases", help_text="List of available application basis slugs"
    )

    attachment_requirements = serializers.SerializerMethodField(
        "get_attachment_requirements", help_text="get the attachment requirements"
    )

    available_benefit_types = serializers.SerializerMethodField(
        "get_available_benefit_types",
        help_text="Available benefit types depend on organization type of the applicant",
    )

    company_contact_person_phone_number = PhoneNumberField(
        allow_blank=True,
        help_text="Company contact person phone number normalized (start with zero, without country code)",
    )

    def get_submitted_at(self, obj):
        if (
            log_entry := obj.log_entries.filter(to_status=ApplicationStatus.RECEIVED)
            .order_by("-created_at")
            .first()
        ):
            return log_entry.created_at
        else:
            return None

    def get_last_modified_at(self, obj):
        if not self.logged_in_user_is_admin() and obj.status != ApplicationStatus.DRAFT:
            return None
        return obj.modified_at

    @extend_schema_field(serializers.ChoiceField(choices=OrganizationType.choices))
    def get_organization_type(self, obj):
        return OrganizationType.resolve_organization_type(obj.company.company_form)

    @extend_schema_field(ApplicationBasisSerializer(many=True))
    def get_available_bases(self, obj):
        return [
            basis.identifier
            for basis in ApplicationBasis.objects.filter(is_active=True)
        ]

    def _get_pay_subsidy_attachment_requirements(self, application):
        req = []
        if application.pay_subsidy_percent:
            req.append(
                (AttachmentType.PAY_SUBSIDY_DECISION, AttachmentRequirement.REQUIRED)
            )
        if application.additional_pay_subsidy_percent:
            req.append(
                (AttachmentType.PAY_SUBSIDY_DECISION, AttachmentRequirement.REQUIRED)
            )
        return req

    def get_attachment_requirements(self, obj):
        if obj.apprenticeship_program:
            return [
                (AttachmentType.EMPLOYMENT_CONTRACT, AttachmentRequirement.REQUIRED),
                (AttachmentType.EDUCATION_CONTRACT, AttachmentRequirement.REQUIRED),
                (
                    AttachmentType.HELSINKI_BENEFIT_VOUCHER,
                    AttachmentRequirement.OPTIONAL,
                ),
            ] + self._get_pay_subsidy_attachment_requirements(obj)
        elif obj.benefit_type in [
            BenefitType.EMPLOYMENT_BENEFIT,
            BenefitType.SALARY_BENEFIT,
        ]:
            return [
                (AttachmentType.EMPLOYMENT_CONTRACT, AttachmentRequirement.REQUIRED),
                (
                    AttachmentType.HELSINKI_BENEFIT_VOUCHER,
                    AttachmentRequirement.OPTIONAL,
                ),
            ] + self._get_pay_subsidy_attachment_requirements(obj)
        elif obj.benefit_type == BenefitType.COMMISSION_BENEFIT:
            return [
                (AttachmentType.COMMISSION_CONTRACT, AttachmentRequirement.REQUIRED),
                (
                    AttachmentType.HELSINKI_BENEFIT_VOUCHER,
                    AttachmentRequirement.OPTIONAL,
                ),
            ]
        elif not obj.benefit_type:
            # applicant has not selected the value yet
            return []
        else:
            raise BenefitAPIException(_("This should be unreachable"))

    def _validate_de_minimis_aid_set(
        self,
        company,
        de_minimis_aid,
        de_minimis_aid_set,
        association_has_business_activities,
    ):
        """
        Validate the de minimis aid parameters:
        * company: the organization applying for the benefit
        * de_minimis_aid: boolean yes/no/null value
        * de_minimis_aid_set: the DeMinimisAid objects represented as list of dicts
          (at this point, the individual dicts have been already valided by DeMinimisAidSerializer
        """
        if (
            OrganizationType.resolve_organization_type(company.company_form)
            == OrganizationType.ASSOCIATION
            and de_minimis_aid is not None
            and not association_has_business_activities
        ):
            raise serializers.ValidationError(
                {
                    "de_minimis_aid_set": _(
                        "This application has non-null de_minimis_aid but is applied by an association"
                    )
                }
            )

        if de_minimis_aid and not de_minimis_aid_set:
            raise serializers.ValidationError(
                {
                    "de_minimis_aid_set": _(
                        "This application has de_minimis_aid set but does not define any"
                    )
                }
            )

        if de_minimis_aid in (None, False) and de_minimis_aid_set:
            raise serializers.ValidationError(
                {
                    "de_minimis_aid_set": _(
                        "This application can not have de minimis aid"
                    )
                }
            )

        total_aid = sum([item["amount"] for item in de_minimis_aid_set])
        if total_aid > DeMinimisAidSerializer.MAX_AID_AMOUNT:
            raise serializers.ValidationError(
                {"de_minimis_aid_set": _("Total amount of de minimis aid too large")}
            )

    def _validate_date_range(self, start_date, end_date, benefit_type):
        # keeping all start/end date validation together
        if start_date and start_date < date(date.today().year, 1, 1):
            raise serializers.ValidationError(
                {"start_date": _("start_date must be within the current year")}
            )
        if end_date:
            if end_date < date(date.today().year, 1, 1):
                raise serializers.ValidationError(
                    {"end_date": _("end_date must be within the current year")}
                )
            if start_date:
                if end_date < start_date:
                    raise serializers.ValidationError(
                        {
                            "end_date": _(
                                "application end_date can not be less than start_date"
                            )
                        }
                    )
                if (
                    benefit_type != BenefitType.COMMISSION_BENEFIT
                    and start_date + relativedelta(months=1) - relativedelta(days=1)
                    > end_date
                ):
                    # A commission can have very short duration and doesn't have the 1 month minimum period as the
                    # employment and salary based benefits.
                    # These two option have identical duration periods which need to be between 1-12 months.
                    # (note: we'll allow full month ranges, like 2021-02-01 - 2021-02-28
                    raise serializers.ValidationError(
                        {"end_date": _("minimum duration of the benefit is one month")}
                    )
                if start_date + relativedelta(months=12) <= end_date:
                    raise serializers.ValidationError(
                        {"end_date": _("maximum duration of the benefit is 12 months")}
                    )

    def _validate_co_operation_negotiations(
        self, co_operation_negotiations, co_operation_negotiations_description
    ):
        if not co_operation_negotiations and co_operation_negotiations_description:
            raise serializers.ValidationError(
                {
                    "co_operation_negotiations_description": _(
                        "This application can not have a description for co-operation negotiations"
                    )
                }
            )

    def _validate_pay_subsidy(
        self, pay_subsidy_granted, pay_subsidy_percent, additional_pay_subsidy_percent
    ):
        if pay_subsidy_granted and pay_subsidy_percent is None:
            raise serializers.ValidationError(
                {"pay_subsidy_percent": _("Pay subsidy percent required")}
            )
        if not pay_subsidy_granted:
            for key in ["pay_subsidy_percent", "additional_pay_subsidy_percent"]:
                if locals()[key] is not None:
                    raise serializers.ValidationError(
                        {
                            key: format_lazy(
                                _("This application can not have {key}"), key=key
                            )
                        }
                    )
        if pay_subsidy_percent is None and additional_pay_subsidy_percent is not None:
            raise serializers.ValidationError(
                {
                    "additional_pay_subsidy_percent": _(
                        "This application can not have additional_pay_subsidy_percent"
                    )
                }
            )

    # Fields that may be null/blank while the application is draft, but
    # must be filled before submitting the application for processing
    REQUIRED_FIELDS_FOR_SUBMITTED_APPLICATIONS = [
        "company_bank_account_number",
        "company_contact_person_phone_number",
        "company_contact_person_email",
        "company_contact_person_first_name",
        "company_contact_person_last_name",
        "co_operation_negotiations",
        "pay_subsidy_granted",
        "apprenticeship_program",
        "de_minimis_aid",
        "benefit_type",
        "start_date",
        "end_date",
        "bases",
    ]

    def _validate_non_draft_required_fields(self, data):
        if data["status"] == ApplicationStatus.DRAFT:
            return
        # must have start_date and end_date before status can change
        # newly created applications are always DRAFT
        required_fields = self.REQUIRED_FIELDS_FOR_SUBMITTED_APPLICATIONS[:]
        if (
            OrganizationType.resolve_organization_type(
                self.get_company(data).company_form
            )
            == OrganizationType.ASSOCIATION
        ):
            required_fields.append("association_has_business_activities")

        for field_name in required_fields:
            if data[field_name] in [None, "", []]:
                raise serializers.ValidationError(
                    {
                        field_name: _(
                            "This field is required before submitting the application"
                        )
                    }
                )

    def _validate_association_has_business_activities(
        self, company, association_has_business_activities
    ):
        if (
            OrganizationType.resolve_organization_type(company.company_form)
            == OrganizationType.COMPANY
            and association_has_business_activities is not None
        ):
            raise serializers.ValidationError(
                {
                    "association_has_business_activities": _(
                        "This field can be set for associations only"
                    )
                }
            )

    @extend_schema_field(serializers.ChoiceField(choices=BenefitType.choices))
    def get_available_benefit_types(self, obj):
        return [
            str(item)
            for item in ApplicationSerializer._get_available_benefit_types(
                obj.company,
                obj.association_has_business_activities,
                obj.apprenticeship_program,
            )
        ]

    def _validate_benefit_type(
        self,
        company,
        benefit_type,
        association_has_business_activities,
        apprenticeship_program,
    ):
        if benefit_type == "":
            return
        if benefit_type not in ApplicationSerializer._get_available_benefit_types(
            company, association_has_business_activities, apprenticeship_program
        ):
            raise serializers.ValidationError(
                {"benefit_type": _("This benefit type can not be selected")}
            )

    @staticmethod
    def _get_available_benefit_types(
        company, association_has_business_activities, apprenticeship_program
    ):
        """
        Make the logic of determining available benefit types available both for generating the list of
        benefit types and validating the incoming data
        """
        if (
            OrganizationType.resolve_organization_type(company.company_form)
            == OrganizationType.ASSOCIATION
            and not association_has_business_activities
        ):
            return [BenefitType.SALARY_BENEFIT]
        else:
            if apprenticeship_program:
                return [
                    BenefitType.SALARY_BENEFIT,
                    BenefitType.EMPLOYMENT_BENEFIT,
                ]
            else:
                return [
                    BenefitType.SALARY_BENEFIT,
                    BenefitType.COMMISSION_BENEFIT,
                    BenefitType.EMPLOYMENT_BENEFIT,
                ]

    def validate(self, data):
        """ """
        company = self.get_company(data)
        self._validate_date_range(
            data.get("start_date"), data.get("end_date"), data.get("benefit_type")
        )
        self._validate_co_operation_negotiations(
            data.get("co_operation_negotiations"),
            data.get("co_operation_negotiations_description"),
        )
        self._validate_pay_subsidy(
            data.get("pay_subsidy_granted"),
            data.get("pay_subsidy_percent"),
            data.get("additional_pay_subsidy_percent"),
        )
        self._validate_de_minimis_aid_set(
            company,
            data.get("de_minimis_aid"),
            data.get("de_minimis_aid_set"),
            data.get("association_has_business_activities"),
        )
        self._validate_association_has_business_activities(
            company, data.get("association_has_business_activities")
        )
        self._validate_benefit_type(
            company,
            data.get("benefit_type", ""),
            data.get("association_has_business_activities"),
            data.get("apprenticeship_program"),
        )
        self._validate_non_draft_required_fields(data)
        return data

    def handle_status_transition(self, instance, previous_status):
        if instance.status == ApplicationStatus.RECEIVED:
            # moving out of DRAFT or ADDITIONAL_INFORMATION_NEEDED, so the applicant
            # may have modified the application
            self._validate_attachments(instance)
        ApplicationLogEntry.objects.create(
            application=instance,
            from_status=previous_status,
            to_status=instance.status,
        )

    def _validate_attachments(self, instance):
        """
        The requirements for attachments are the minimum requirements.
        * Sometimes, a multi-page document might be uploaded as a set of jpg files, and the backend
          would not know that it's meant to be a single document.
        * If the applicant uploads more than the maximum number of attachments of a certain type, that is allowed.
        * If wrong types of attachments have been uploaded, they are purged from the system. This might happen
          if the applicant first uploads attachments, but then goes back to previous steps and changes certain
          application fields before submitting the application
        """

        attachment_requirements = self.get_attachment_requirements(instance)
        required_attachment_types = [
            req[0]
            for req in attachment_requirements
            if req[1] == AttachmentRequirement.REQUIRED
        ]
        valid_attachment_types = {req[0] for req in attachment_requirements}
        attachments_with_invalid_type = []

        for attachment in instance.attachments.all().order_by("created_at"):
            if attachment.attachment_type not in valid_attachment_types:
                attachments_with_invalid_type.append(attachment)
            else:
                if attachment.attachment_type in required_attachment_types:
                    required_attachment_types.remove(attachment.attachment_type)

        if required_attachment_types:
            # if anything still remains in the list, it means some attachment(s) were missing
            raise serializers.ValidationError(
                _("Application does not have required attachments")
            )
        for attach in attachments_with_invalid_type:
            attach.delete()

    @transaction.atomic
    def update(self, instance, validated_data):
        de_minimis_data = validated_data.pop("de_minimis_aid_set", None)
        employee_data = validated_data.pop("employee", None)
        pre_update_status = instance.status
        application = super().update(instance, validated_data)
        if de_minimis_data is not None:
            # if it is a patch request that didn't have de_minimis_data_set, do nothing
            self._update_de_minimis_aid(application, de_minimis_data)
        if employee_data is not None:
            self._update_or_create_employee(application, employee_data)

        if instance.status != pre_update_status:
            self.handle_status_transition(instance, pre_update_status)

        return application

    @transaction.atomic
    def create(self, validated_data):
        if validated_data["status"] != ApplicationStatus.DRAFT:
            raise serializers.ValidationError(
                _("Application initial state must be draft")
            )
        de_minimis_data = validated_data.pop("de_minimis_aid_set")
        employee_data = validated_data.pop("employee", None)
        validated_data["company"] = self.get_company_for_new_application(validated_data)
        application = super().create(validated_data)
        self.assign_default_fields_from_company(application, validated_data["company"])
        self._update_de_minimis_aid(application, de_minimis_data)
        self._update_or_create_employee(application, employee_data)
        return application

    def _update_or_create_employee(self, application, employee_data):
        employee, created = Employee.objects.update_or_create(
            application=application, defaults=employee_data
        )
        return employee

    def get_company_for_new_application(self, validated_data):
        """
        Company field is read_only. When creating a new application, assign company.
        """
        if self.logged_in_user_is_admin():
            # Only handlers can create applications for any company
            return Company.objects.get(validated_data["create_application_for_company"])
        else:
            return self.get_logged_in_user_company()

    def get_company(self, validated_data):
        if self.instance:
            return self.instance.company
        else:
            return self.get_company_for_new_application(validated_data)

    def assign_default_fields_from_company(self, application, company):
        application.company_name = company.name
        application.company_form = company.company_form
        application.official_company_street_address = company.street_address
        application.official_company_postcode = company.postcode
        application.official_company_city = company.city
        application.save()

    def _update_de_minimis_aid(self, application, de_minimis_data):
        serializer = DeMinimisAidSerializer(data=de_minimis_data, many=True)
        if not serializer.is_valid():
            raise BenefitAPIException(
                format_lazy(
                    _("Reading de minimis data failed: {errors}"),
                    errors=serializer.errors,
                )
            )
        # Clear the previous DeMinimisAid objects from the database.
        # The request must always contain all the DeMinimisAid objects for this application.
        application.de_minimis_aid_set.all().delete()
        for idx, aid_item in enumerate(serializer.validated_data):
            aid_item["application_id"] = application.pk
            aid_item[
                "ordering"
            ] = idx  # use the ordering defined in the JSON sent by the client
        serializer.save()

    def logged_in_user_is_admin(self):
        # TODO: user management
        return False

    def get_logged_in_user_company(self):
        # TODO: user management
        return Company.objects.all().order_by("pk").first()