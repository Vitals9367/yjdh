import io
import uuid
import zipfile
from datetime import date
from typing import List
from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import FileResponse
from django.urls import reverse

from applications.api.v1.ahjo_integration_views import AhjoAttachmentView
from applications.enums import (
    AhjoCallBackStatus,
    AhjoStatus,
    ApplicationStatus,
    BenefitType,
)
from applications.models import Application
from applications.services.ahjo_integration import (
    ACCEPTED_TITLE,
    export_application_batch,
    ExportFileInfo,
    generate_composed_files,
    generate_single_approved_file,
    generate_single_declined_file,
    get_application_for_ahjo,
    REJECTED_TITLE,
)
from applications.tests.factories import ApplicationFactory, DecidedApplicationFactory
from calculator.models import Calculation
from calculator.tests.factories import PaySubsidyFactory
from companies.tests.factories import CompanyFactory
from helsinkibenefit.tests.conftest import *  # noqa
from shared.common.tests.utils import normalize_whitespace
from shared.service_bus.enums import YtjOrganizationCode
from users.models import User

DE_MINIMIS_AID_PARTIAL_TEXT = (
    # In English ~= "support is granted as insignificant i.e. de minimis support"
    "tuki myönnetään vähämerkityksisenä eli ns. de minimis -tukena"
)


def _assert_html_content(html, include_keys=(), excluded_keys=()):
    for k in include_keys:
        assert k in html
    for k in excluded_keys:
        assert k not in html


@pytest.mark.parametrize(
    "company_form_code,company_form,should_show_de_minimis_aid_footer",
    [
        (
            YtjOrganizationCode.ASSOCIATION_FORM_CODE_DEFAULT,
            "ry",
            False,
        ),
        (
            YtjOrganizationCode.COMPANY_FORM_CODE_DEFAULT,
            "oy",
            False,
        ),
        (
            YtjOrganizationCode.COMPANY_FORM_CODE_DEFAULT,
            "oy",
            True,
        ),
        (YtjOrganizationCode.COMPANY_FORM_CODE_DEFAULT, "oy", True),
    ],
)
@patch("applications.services.ahjo_integration.pdfkit.from_string")
def test_generate_single_approved_template_html(
    mock_pdf_convert,
    company_form_code: YtjOrganizationCode,
    company_form: str,
    should_show_de_minimis_aid_footer: bool,
):
    mock_pdf_convert.return_value = {}
    company = CompanyFactory(
        company_form_code=company_form_code, company_form=company_form
    )
    apps: List[Application] = [
        DecidedApplicationFactory(
            company=company,
            status=ApplicationStatus.ACCEPTED,
        )
    ]
    for app in apps:
        app.calculation.calculated_benefit_amount = 1000
        app.calculation.granted_as_de_minimis_aid = should_show_de_minimis_aid_footer
        app.calculation.save()
    # Only assert html content for easier comparison
    html = generate_single_approved_file(apps[0].company, apps, 3).html_content
    for app in apps:
        _assert_html_content(
            html,
            (
                app.ahjo_application_number,
                app.employee.first_name,
                app.employee.last_name,
            ),
        )
    whitespace_normalized_html = normalize_whitespace(html)
    assert (
        normalize_whitespace(ACCEPTED_TITLE).casefold()
        in whitespace_normalized_html.casefold()
    )
    assert (
        DE_MINIMIS_AID_PARTIAL_TEXT.casefold() in whitespace_normalized_html.casefold()
    ) == should_show_de_minimis_aid_footer


@patch("applications.services.ahjo_integration.pdfkit.from_string")
def test_generate_single_declined_template_html(mock_pdf_convert):
    mock_pdf_convert.return_value = {}
    company = CompanyFactory()
    apps = ApplicationFactory.create_batch(
        3, company=company, status=ApplicationStatus.REJECTED
    )
    # Only assert html content for easier comparison
    html = generate_single_declined_file(apps[0].company, apps, 4).html_content
    for app in apps:
        _assert_html_content(
            html,
            (
                app.ahjo_application_number,
                app.employee.first_name,
                app.employee.last_name,
            ),
        )

    whitespace_normalized_html = normalize_whitespace(html)
    assert (
        normalize_whitespace(REJECTED_TITLE).casefold()
        in whitespace_normalized_html.casefold()
    )
    assert (
        DE_MINIMIS_AID_PARTIAL_TEXT.casefold()
        not in whitespace_normalized_html.casefold()
    )


@patch("applications.services.ahjo_integration.pdfkit.from_string")
def test_generate_composed_template_html(mock_pdf_convert):
    mock_pdf_convert.return_value = {}
    accepted_app_1 = DecidedApplicationFactory(
        status=ApplicationStatus.ACCEPTED,
        start_date=date.today(),
    )
    accepted_app_1.calculation.calculated_benefit_amount = 1000
    accepted_app_1.calculation.save()
    accepted_app_2 = DecidedApplicationFactory(
        status=ApplicationStatus.ACCEPTED,
        start_date=date.today(),
    )
    accepted_app_2.calculation.calculated_benefit_amount = 1000
    accepted_app_2.calculation.save()
    rejected_app_1 = DecidedApplicationFactory(
        status=ApplicationStatus.REJECTED, start_date=date.today()
    )
    rejected_app_2 = DecidedApplicationFactory(
        status=ApplicationStatus.REJECTED, start_date=date.today()
    )

    # Only assert html content for easier comparison
    files: List[ExportFileInfo] = generate_composed_files(
        [accepted_app_1, accepted_app_2], [rejected_app_1, rejected_app_2], 5
    )
    assert len(files) == 4

    # files[0]: Public accepted composed files
    # files[1]: Private accepted composed files
    # files[2]: Private rejected composed files
    _assert_html_content(
        files[0].html_content,
        (
            accepted_app_1.ahjo_application_number,
            accepted_app_2.ahjo_application_number,
        ),
        (
            rejected_app_1.ahjo_application_number,
            rejected_app_2.ahjo_application_number,
            accepted_app_1.employee.first_name,
            accepted_app_2.employee.first_name,
        ),
    )
    _assert_html_content(
        files[1].html_content,
        (
            accepted_app_1.ahjo_application_number,
            accepted_app_2.ahjo_application_number,
        ),
        (rejected_app_1.ahjo_application_number,),
    )
    _assert_html_content(
        files[2].html_content,
        (
            rejected_app_1.ahjo_application_number,
            rejected_app_2.ahjo_application_number,
        ),
        (
            accepted_app_1.ahjo_application_number,
            accepted_app_2.ahjo_application_number,
        ),
    )


def test_export_application_batch(application_batch):
    application_batch.applications.add(
        DecidedApplicationFactory.create(
            status=ApplicationStatus.ACCEPTED,
            calculation__calculated_benefit_amount=1000,
        )
    )
    application_batch.applications.add(
        DecidedApplicationFactory.create(status=ApplicationStatus.REJECTED)
    )
    application_batch.applications.add(
        DecidedApplicationFactory.create(status=ApplicationStatus.CANCELLED)
    )
    zip_file = export_application_batch(application_batch)
    file_like_object = io.BytesIO(zip_file)
    archive = zipfile.ZipFile(file_like_object)
    assert (
        len(archive.infolist())
        == application_batch.applications.exclude(
            status=ApplicationStatus.CANCELLED
        ).count()
        + 4
    )


@patch("applications.services.ahjo_integration.pdfkit.from_string")
def test_multiple_benefit_per_application(mock_pdf_convert):
    mock_pdf_convert.return_value = {}
    # Test case data and expected results collected from
    # calculator/tests/Helsinki-lisa laskurin testitapaukset.xlsx/ Sheet Palkan Helsinki-lisä / Column E
    application = ApplicationFactory(
        association_has_business_activities=True,
        company__company_form="ry",
        company__company_form_code=YtjOrganizationCode.ASSOCIATION_FORM_CODE_DEFAULT,
        start_date=date(2021, 7, 10),
        end_date=date(2021, 11, 10),
        status=ApplicationStatus.RECEIVED,
        benefit_type=BenefitType.SALARY_BENEFIT,
    )

    application.calculation = Calculation(
        application=application,
        monthly_pay=3200,
        vacation_money=0,
        other_expenses=200,
        start_date=application.start_date,
        end_date=application.end_date,
        state_aid_max_percentage=50,
        calculated_benefit_amount=0,
        override_monthly_benefit_amount=None,
    )
    pay_subsidy = PaySubsidyFactory(
        pay_subsidy_percent=50, start_date=date(2021, 7, 10), end_date=date(2021, 9, 10)
    )
    application.pay_subsidies.add(pay_subsidy)
    application.save()
    application.calculation.save()
    application.refresh_from_db()
    application.calculation.init_calculator()
    application.calculation.calculate()
    html = generate_single_approved_file(
        application.company, [application], 6
    ).html_content
    assert (
        html.count(application.ahjo_application_number) == 2
    )  # Make sure there are two rows in the report
    print(html)
    _assert_html_content(
        html,
        (
            application.ahjo_application_number,
            application.employee.first_name,
            application.employee.last_name,
            "440",
            "893",
            "1600",
            "800",
            "2493",
        ),
    )


def test_prepare_ahjo_file_response(decided_application):
    attachment = decided_application.attachments.first()
    response = AhjoAttachmentView._prepare_file_response(attachment)

    assert isinstance(response, FileResponse)

    assert response["Content-Length"] == f"{attachment.attachment_file.size}"
    assert (
        response["Content-Disposition"]
        == f"attachment; filename={attachment.attachment_file.name}"
    )
    assert response["Content-Type"] == f"{attachment.content_type}"


@pytest.fixture
def attachment(decided_application):
    return decided_application.attachments.first()


def test_get_attachment_success(ahjo_client, attachment, ahjo_user_token, settings):
    settings.NEXT_PUBLIC_MOCK_FLAG = True
    url = reverse("ahjo_attachment_url", kwargs={"uuid": attachment.id})

    auth_headers = {"HTTP_AUTHORIZATION": "Token " + ahjo_user_token.key}

    response = ahjo_client.get(url, **auth_headers)

    assert response.status_code == 200
    assert response["Content-Type"] == f"{attachment.content_type}"
    assert response["Content-Length"] == f"{attachment.attachment_file.size}"
    assert (
        response["Content-Disposition"]
        == f"attachment; filename={attachment.attachment_file.name}"
    )


def test_get_attachment_not_found(ahjo_client, ahjo_user_token, settings):
    settings.NEXT_PUBLIC_MOCK_FLAG = True
    id = uuid.uuid4()
    url = reverse("ahjo_attachment_url", kwargs={"uuid": id})
    auth_headers = {"HTTP_AUTHORIZATION": "Token " + ahjo_user_token.key}

    response = ahjo_client.get(url, **auth_headers)

    assert response.status_code == 404


def test_get_attachment_unauthorized_wrong_or_missing_credentials(
    anonymous_client, attachment, settings
):
    settings.NEXT_PUBLIC_MOCK_FLAG = True
    # without any auth headers
    url = reverse("ahjo_attachment_url", kwargs={"uuid": attachment.id})
    response = anonymous_client.get(url)

    assert response.status_code == 401
    # with incorrect auth token
    response = anonymous_client.get(
        url,
        headers={"Authorization": "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"},
    )
    assert response.status_code == 401


def test_get_attachment_unauthorized_ip_not_allowed(
    ahjo_client, ahjo_user_token, attachment, settings
):
    settings.NEXT_PUBLIC_MOCK_FLAG = False
    url = reverse("ahjo_attachment_url", kwargs={"uuid": attachment.id})
    auth_headers = {"HTTP_AUTHORIZATION": "Token " + ahjo_user_token.key}

    response = ahjo_client.get(url, **auth_headers)
    assert response.status_code == 403


@pytest.mark.django_db
def test_ahjo_callback_success(
    ahjo_client, ahjo_user_token, decided_application, settings
):
    settings.NEXT_PUBLIC_MOCK_FLAG = True
    auth_headers = {"HTTP_AUTHORIZATION": "Token " + ahjo_user_token.key}
    callback_payload = {
        "message": AhjoCallBackStatus.SUCCESS,
        "requestId": f"{uuid.uuid4()}",
        "caseId": "HEL 2023-999999",
        "caseGuid": f"{uuid.uuid4()}",
    }
    url = reverse("ahjo_callback_url", kwargs={"uuid": decided_application.id})
    response = ahjo_client.post(url, **auth_headers, data=callback_payload)

    decided_application.refresh_from_db()
    assert response.status_code == 200
    assert response.data == {"message": "Callback received"}
    assert decided_application.ahjo_case_id == callback_payload["caseId"]
    assert str(decided_application.ahjo_case_guid) == callback_payload["caseGuid"]
    assert decided_application.ahjo_status.latest().status == AhjoStatus.CASE_OPENED


def test_ahjo_callback_unauthorized_wrong_or_missing_credentials(
    anonymous_client, decided_application, settings
):
    settings.NEXT_PUBLIC_MOCK_FLAG = True
    url = reverse("ahjo_callback_url", kwargs={"uuid": decided_application.id})
    response = anonymous_client.post(url)

    assert response.status_code == 401
    response = anonymous_client.post(
        url,
        headers={"Authorization": "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"},
    )
    assert response.status_code == 401


def test_ahjo_callback_unauthorized_ip_not_allowed(
    ahjo_client, ahjo_user_token, decided_application, settings
):
    settings.NEXT_PUBLIC_MOCK_FLAG = False
    url = reverse("ahjo_callback_url", kwargs={"uuid": decided_application.id})
    auth_headers = {"HTTP_AUTHORIZATION": "Token " + ahjo_user_token.key}

    response = ahjo_client.post(url, **auth_headers)
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_application_for_ahjo_success(decided_application):
    user = decided_application.calculation.handler
    User.objects.filter(pk=user.id).update(ad_username="foobar")
    assert get_application_for_ahjo(decided_application.id) == decided_application


@pytest.mark.django_db
def test_get_application_for_ahjo_no_application():
    # Try to get an application with a non-existing id
    with pytest.raises(ObjectDoesNotExist):
        get_application_for_ahjo(uuid.uuid4())


@pytest.mark.django_db
def test_get_application_for_ahjo_no_ad_username(decided_application):
    # Try to get an application with a handler that has no ad_username
    with pytest.raises(ImproperlyConfigured):
        get_application_for_ahjo(decided_application.id)
