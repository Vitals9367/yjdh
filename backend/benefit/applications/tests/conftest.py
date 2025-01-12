import os
import random
from datetime import timedelta

import factory
import pytest
from django.conf import settings
from django.utils import timezone

from applications.enums import ApplicationStatus, BenefitType
from applications.models import Application
from applications.services.ahjo_payload import prepare_open_case_payload
from applications.services.applications_csv_report import ApplicationsCsvService
from applications.tests.factories import (
    ApplicationBatchFactory,
    ApplicationFactory,
    CancelledApplicationFactory,
    DecidedApplicationFactory,
    EmployeeFactory,
    HandlingApplicationFactory,
    ReceivedApplicationFactory,
)
from common.tests.conftest import *  # noqa
from companies.tests.conftest import *  # noqa
from helsinkibenefit.tests.conftest import *  # noqa
from shared.service_bus.enums import YtjOrganizationCode
from terms.tests.conftest import *  # noqa
from terms.tests.factories import TermsOfServiceApprovalFactory


@pytest.fixture
def anonymous_application():
    with factory.Faker.override_default_locale("fi_FI"):
        return ApplicationFactory()


@pytest.fixture
def anonymous_handling_application():
    with factory.Faker.override_default_locale("fi_FI"):
        return HandlingApplicationFactory()


@pytest.fixture
def received_application(mock_get_organisation_roles_and_create_company):
    with factory.Faker.override_default_locale("fi_FI"):
        return ReceivedApplicationFactory(
            company=mock_get_organisation_roles_and_create_company
        )


@pytest.fixture
def handling_application(mock_get_organisation_roles_and_create_company):
    with factory.Faker.override_default_locale("fi_FI"):
        return HandlingApplicationFactory(
            company=mock_get_organisation_roles_and_create_company
        )


@pytest.fixture
def decided_application(mock_get_organisation_roles_and_create_company):
    with factory.Faker.override_default_locale("fi_FI"):
        return DecidedApplicationFactory(
            company=mock_get_organisation_roles_and_create_company
        )


@pytest.fixture
def application_batch():
    with factory.Faker.override_default_locale("fi_FI"):
        return ApplicationBatchFactory()


@pytest.fixture
def talpa_service(application_batch):
    return ApplicationsCsvService([application_batch])


@pytest.fixture
def talpa_service_with_one_application(talpa_service):
    talpa_service.get_applications().first().delete()
    assert talpa_service.get_applications().count() == 1
    return talpa_service


@pytest.fixture
def applications_csv_service():
    # retrieve the objects through the default manager so that annotations are added
    application1 = DecidedApplicationFactory(application_number=100001)
    application2 = DecidedApplicationFactory(application_number=100002)
    return ApplicationsCsvService(
        Application.objects.filter(pk__in=[application1.pk, application2.pk]).order_by(
            "application_number"
        )
    )


@pytest.fixture
def applications_csv_service_with_one_application(applications_csv_service):
    application1 = DecidedApplicationFactory(application_number=100001)
    return ApplicationsCsvService(Application.objects.filter(pk=application1.pk))


@pytest.fixture
def pruned_applications_csv_service():
    # retrieve the objects through the default manager so that annotations are added
    application1 = DecidedApplicationFactory(application_number=100001)
    application2 = DecidedApplicationFactory(application_number=100002)
    return ApplicationsCsvService(
        Application.objects.filter(pk__in=[application1.pk, application2.pk]).order_by(
            "application_number"
        ),
        True,
    )


@pytest.fixture
def pruned_applications_csv_service_with_one_application(
    applications_csv_service, application_batch
):
    application1 = application_batch.applications.all().first()
    return ApplicationsCsvService(Application.objects.filter(pk=application1.pk), True)


@pytest.fixture
def applications_csv_with_no_applications():
    return ApplicationsCsvService([])


@pytest.fixture
def employee():
    with factory.Faker.override_default_locale("fi_FI"):
        return EmployeeFactory()


@pytest.fixture
def application(mock_get_organisation_roles_and_create_company):
    # Application which belongs to logged in user company
    with factory.Faker.override_default_locale("fi_FI"):
        app = ApplicationFactory()
        app.company = mock_get_organisation_roles_and_create_company
        app.save()
        return app


@pytest.fixture
def association_application(mock_get_organisation_roles_and_create_company):
    """
    :return: A valid application by an association
    """
    application = ApplicationFactory()
    application.company = mock_get_organisation_roles_and_create_company
    application.save()
    application.company.company_form = (
        YtjOrganizationCode.ASSOCIATION_FORM_CODE_DEFAULT.label
    )
    application.company.company_form_code = (
        YtjOrganizationCode.ASSOCIATION_FORM_CODE_DEFAULT
    )
    application.company.save()
    application.benefit_type = BenefitType.SALARY_BENEFIT
    application.de_minimis_aid = None
    application.association_has_business_activities = False
    application.de_minimis_aid_set.all().delete()
    return application


@pytest.fixture()
def accept_tos(
    bf_user, mock_get_organisation_roles_and_create_company, terms_of_service
):
    return TermsOfServiceApprovalFactory(
        user=bf_user,
        company=mock_get_organisation_roles_and_create_company,
        terms=terms_of_service,
    )


@pytest.fixture()
def cancelled_applications():
    for _ in range(5):
        CancelledApplicationFactory()

    applications = Application.objects.filter(status=ApplicationStatus.CANCELLED)
    yield applications
    for application in applications:
        _delete_attachments(application)


@pytest.fixture()
def cancelled_delete_date():
    """Return a random date between 30 and 365 days ago"""
    return timezone.now() - timedelta(days=random.randint(30, 365))


@pytest.fixture()
def cancelled_to_delete(cancelled_delete_date, cancelled_applications):
    cancelled_applications.update(modified_at=cancelled_delete_date)
    yield cancelled_applications


@pytest.fixture()
def draft_applications():
    for _ in range(5):
        ApplicationFactory()

    applications = Application.objects.filter(status=ApplicationStatus.DRAFT)
    yield applications
    for application in applications:
        _delete_attachments(application)


@pytest.fixture()
def draft_delete_date():
    """Return a random date between 180 and 365 days ago"""
    return timezone.now() - timedelta(days=random.randint(180, 365))


@pytest.fixture()
def drafts_to_delete(draft_delete_date, draft_applications):
    draft_applications.update(modified_at=draft_delete_date)
    yield draft_applications


@pytest.fixture()
def draft_keep_date():
    return timezone.now() - timedelta(days=random.randint(1, 59))


@pytest.fixture()
def drafts_to_keep(draft_keep_date, draft_applications):
    draft_applications.update(modified_at=draft_keep_date)
    yield draft_applications


@pytest.fixture()
def draft_notification_date():
    return timezone.now() - timedelta(days=166)


@pytest.fixture()
def drafts_about_to_be_deleted(draft_notification_date, draft_applications):
    draft_applications.update(modified_at=draft_notification_date)
    yield draft_applications


@pytest.fixture(autouse=True)
def auto_accept_tos(autouse_django_db, accept_tos):
    return accept_tos


@pytest.fixture()
def set_debug_to_true(settings):
    settings.DEBUG = True


@pytest.fixture()
def set_debug_to_false(settings):
    settings.DEBUG = False


@pytest.fixture()
def ahjo_payload_record(decided_application):
    application = decided_application

    record_title = "Hakemus"
    record_type = "hakemus"
    acquired = application.created_at.isoformat()
    reference = str(application.application_number)
    documents = []
    agent = application.calculation.handler
    publicity_class = "Salassa pidettävä"

    return {
        "Title": record_title,
        "Type": record_type,
        "Acquired": acquired,
        "PublicityClass": publicity_class,
        "SecurityReasons": ["JulkL (621/1999) 24.1 § 25 k"],
        "Language": "fi",
        "PersonalData": "Sisältää erityisiä henkilötietoja",
        "Reference": reference,
        "Documents": documents,
        "Agents": [
            {
                "Role": "mainCreator",
                "Name": f"{agent.last_name}, {agent.first_name}",
                "ID": agent.ad_username,
            }
        ],
    }


@pytest.fixture()
def ahjo_open_case_top_level_dict(decided_application):
    application = decided_application
    title = f"Avustuksen myöntäminen, työllisyyspalvelut, \
työnantajan Helsinki-lisä vuonna {application.created_at.year}, \
työnantaja {application.company_name}"

    return {
        "Title": title,
        "Acquired": application.created_at.isoformat(),
        "ClassificationCode": "02 05 01 00",
        "ClassificationTitle": "Kunnan myöntämät avustukset",
        "Language": "fi",
        "PublicityClass": "Julkinen",
        "InternalTitle": f"Avustuksen myöntäminen, työllisyyspalvelut, \
              työnantajan Helsinki-lisä vuonna {application.created_at.year}, \
              työnantaja {application.company_name}",
        "Subjects": [
            {"Subject": "Helsinki-lisät", "Scheme": "hki-yhpa"},
            {"Subject": "kunnan myöntämät avustukset", "Scheme": "hki-yhpa"},
            {"Subject": "työnantajat", "Scheme": "hki-yhpa"},
            {"Subject": "työllisyydenhoito"},
        ],
        "PersonalData": "Sisältää erityisiä henkilötietoja",
        "Reference": application.application_number,
        "Records": [],
        "Agents": [
            {
                "Role": "sender_initiator",
                "CorporateName": application.company.name,
                "ContactPerson": application.contact_person,
                "Type": "ExterOnal",
                "Email": application.company_contact_person_email,
                "AddressStreet": application.company.street_address,
                "AddressPostalCode": application.company.postcode,
                "AddressCity": application.company.city,
            }
        ],
    }


def split_lines_at_semicolon(csv_string):
    # split CSV into lines and columns without using the csv library
    csv_lines = csv_string.splitlines()
    return [line.split(";") for line in csv_lines]


def _delete_attachments(application: Application):
    """Delete attachment files from the given application"""
    for attachment in application.attachments.all():
        attachment.attachment_file.delete()


def pytest_sessionfinish(session, exitstatus):
    # Delete all files in the media folder
    files_in_media = os.listdir(settings.MEDIA_ROOT)
    number_of_files = len(files_in_media)
    for file in files_in_media:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, file))
        except OSError as e:
            print(f"Error while deleting file in media folder: {e}")
    print(f"\nTests finished, deleted {number_of_files} files in the media folder")


@pytest.fixture()
def ahjo_open_case_payload(decided_application):
    return prepare_open_case_payload(decided_application)
