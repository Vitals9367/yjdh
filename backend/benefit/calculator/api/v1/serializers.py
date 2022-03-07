from applications.enums import ApplicationStatus
from calculator.models import (
    Calculation,
    CalculationRow,
    PaySubsidy,
    PreviousBenefit,
    TrainingCompensation,
)
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from users.api.v1.serializers import UserSerializer
from users.models import User


class CalculationRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationRow
        fields = [
            "id",
            "row_type",
            "ordering",
            "description_fi",
            "amount",
        ]
        # CalculationRows are generated by the calculator and not directly editable.
        # Edit the source data instead and recalculate.
        read_only_fields = [
            "id",
            "row_type",
            "ordering",
            "description_fi",
            "amount",
        ]


class CalculationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    rows = CalculationRowSerializer(
        read_only=True,
        many=True,
        help_text="Calculation rows, generated by the calculator",
    )
    handler_details = UserSerializer(
        help_text="The handler object, with fields, currently assigned to this calculation and application (read-only)",
        read_only=True,
        source="handler",
    )
    handler = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=User.objects.filter(is_staff=True),
        write_only=True,
        help_text="Set the handler of this Calculation (write-only)",
    )

    override_monthly_benefit_amount = serializers.DecimalField(
        allow_null=True,
        max_digits=Calculation.override_monthly_benefit_amount.field.max_digits,
        decimal_places=Calculation.override_monthly_benefit_amount.field.decimal_places,
        min_value=0,
        help_text="manually override the monthly benefit amount",
    )

    CALCULATION_MAX_MONTHS = 24

    def _validate_date_range(self, start_date, end_date):
        # Only validate date range if both of them are set
        if not (start_date is None and end_date is None):
            # validation is more relaxed as it's assumed that the handlers know what they're doing
            if (
                start_date + relativedelta(months=self.CALCULATION_MAX_MONTHS)
                <= end_date
            ):
                raise serializers.ValidationError(
                    {"end_date": _("Date range too large")}
                )

    def _validate_override_monthly_benefit_amount_comment(
        self, override_monthly_benefit_amount, override_monthly_benefit_amount_comment
    ):
        if (
            not override_monthly_benefit_amount
            and override_monthly_benefit_amount_comment
        ):
            raise serializers.ValidationError(
                {
                    "override_monthly_benefit_amount_comment": _(
                        "This calculation can not have a override_monthly_benefit_amount_comment"
                    )
                }
            )
        elif (
            override_monthly_benefit_amount
            and not override_monthly_benefit_amount_comment
        ):
            raise serializers.ValidationError(
                {
                    "override_monthly_benefit_amount_comment": _(
                        "This calculation needs override_monthly_benefit_amount_comment"
                    )
                }
            )

    HANDLER_CAN_BE_ASSIGNED_IN_STATUSES = [
        ApplicationStatus.RECEIVED,
        ApplicationStatus.HANDLING,
    ]
    HANDLER_CAN_BE_UNASSIGNED_IN_STATUSES = [
        ApplicationStatus.DRAFT,
        ApplicationStatus.RECEIVED,
        ApplicationStatus.HANDLING,
    ]

    def validate_handler(self, handler):
        if handler is None:
            if (
                self.parent.instance.status
                not in self.HANDLER_CAN_BE_UNASSIGNED_IN_STATUSES
            ):
                raise serializers.ValidationError(
                    _("Handler can not be unassigned in this status")
                )
        else:
            if (
                self.parent.instance.status
                not in self.HANDLER_CAN_BE_ASSIGNED_IN_STATUSES
            ):
                raise serializers.ValidationError(
                    _("Handler can not assigned in this status")
                )
        return handler

    def validate(self, data):
        self._validate_date_range(data.get("start_date"), data.get("end_date"))
        self._validate_override_monthly_benefit_amount_comment(
            data.get("override_monthly_benefit_amount"),
            data.get("override_monthly_benefit_amount_comment"),
        )
        return data

    class Meta:
        model = Calculation
        fields = [
            "id",
            "monthly_pay",
            "vacation_money",
            "other_expenses",
            "start_date",
            "end_date",
            "state_aid_max_percentage",
            "granted_as_de_minimis_aid",
            "target_group_check",
            "calculated_benefit_amount",
            "override_monthly_benefit_amount",
            "override_monthly_benefit_amount_comment",
            "rows",
            "handler_details",
            "handler",
            "duration_in_months_rounded",
        ]
        read_only_fields = [
            "id",
            "calculated_benefit_amount",
            "duration_in_months_rounded",
        ]


class UpdateOrderedListSerializer(serializers.ListSerializer):
    """
    Handle updates of objects with an ordering field.

    https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-update
    """

    def update(self, instance, validated_data):
        # Current instances in the database. Maps for id->instance.
        obj_mapping = {obj.id: obj for obj in instance}
        # A list of ids of the validated data items. IDs do not exist for new instances.
        incoming_ids = [item["id"] for item in validated_data if item.get("id")]

        # Perform deletions before create/update, to avoid conflicting ordering values
        for obj_id, obj in obj_mapping.items():
            if obj_id not in incoming_ids:
                obj.delete()

        # Perform creations and updates.
        ret = []
        for data in validated_data:
            obj = obj_mapping.get(data.get("id"), None)
            if obj is None:
                ret.append(self.child.create(data))
            else:
                ret.append(self.child.update(obj, data))
            # ordering field is not exposed in API, it is added in ApplicantApplicationSerializer
            if ordering := data.get("ordering"):
                ret[-1].ordering = ordering
                ret[-1].save()

        return ret


class PaySubsidySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    work_time_percent = serializers.DecimalField(
        max_digits=PaySubsidy.work_time_percent.field.max_digits,
        decimal_places=PaySubsidy.work_time_percent.field.decimal_places,
        min_value=1,
        max_value=PaySubsidy.DEFAULT_WORK_TIME_PERCENT,
    )

    class Meta:
        model = PaySubsidy
        fields = [
            "id",
            "start_date",
            "end_date",
            "pay_subsidy_percent",
            "work_time_percent",
            "disability_or_illness",
            "duration_in_months_rounded",
        ]
        read_only_fields = [
            "duration_in_months_rounded",
        ]

        list_serializer_class = UpdateOrderedListSerializer


class TrainingCompensationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = TrainingCompensation
        fields = [
            "id",
            "start_date",
            "end_date",
            "monthly_amount",
        ]
        read_only_fields = []

        list_serializer_class = UpdateOrderedListSerializer


class PreviousBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreviousBenefit
        fields = [
            "id",
            "company",
            "social_security_number",
            "start_date",
            "end_date",
            "monthly_amount",
            "total_amount",
        ]
        read_only_fields = []