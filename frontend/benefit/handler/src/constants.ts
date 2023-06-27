import {
  APPLICATION_ORIGINS,
  APPLICATION_STATUSES,
  EMPLOYEE_KEYS,
} from 'benefit-shared/constants';

export enum ROUTES {
  HOME = '/',
  LOGIN = '/login',
  APPLICATION = '/application',
  APPLICATION_FORM = '/new-application',

  // temporary urls, not defined yet
  APPLICATIONS_BATCHES = '/batches',
  APPLICATIONS_ARCHIVE = '/archive',
  APPLICATIONS_REPORTS = '/reports',
}

export enum EXPORT_APPLICATIONS_ROUTES {
  ACCEPTED = 'export_new_accepted_applications',
  REJECTED = 'export_new_rejected_applications',
  IN_TIME_RANGE = 'export_csv',
}

export enum SUPPORTED_LANGUAGES {
  FI = 'fi',
  SV = 'sv',
  EN = 'en',
}

export const DEFAULT_LANGUAGE = SUPPORTED_LANGUAGES.FI;

export const COMMON_I18N_NAMESPACES = ['common'] as const;

export const PRIVACY_POLICY_LINKS = {
  fi: 'https://www.hel.fi/1',
  en: 'https://www.hel.fi/2',
  sv: 'https://www.hel.fi/3',
} as const;

export enum EXPORT_APPLICATIONS_IN_TIME_RANGE_FORM_KEYS {
  START_DATE = 'startDate',
  END_DATE = 'endDate',
}

export enum CALCULATION_SALARY_KEYS {
  START_DATE = 'startDate',
  END_DATE = 'endDate',
  MONTHLY_PAY = 'monthlyPay',
  OTHER_EXPENSES = 'otherExpenses',
  VACATION_MONEY = 'vacationMoney',
  STATE_AID_MAX_PERCENTAGE = 'stateAidMaxPercentage',
  PAY_SUBSIDY_PERCENT = 'paySubsidyPercent',
  OVERRIDE_MONTHLY_BENEFIT_AMOUNT = 'overrideMonthlyBenefitAmount',
  OVERRIDE_MONTHLY_BENEFIT_AMOUNT_COMMENT = 'overrideMonthlyBenefitAmountComment',
  // eslint-disable-next-line no-secrets/no-secrets
  WORK_TIME_PERCENT = 'workTimePercent',
  PAY_SUBSIDIES = 'paySubsidies',
  TRAINING_COMPENSATIONS = 'trainingCompensations',
  MONTHLY_AMOUNT = 'monthlyAmount',
}

export const STATE_AID_MAX_PERCENTAGE_OPTIONS = [50, 100];

export const CALCULATION_SUMMARY_ROW_TYPES = [
  'state_aid_max_monthly_eur',
  'pay_subsidy_monthly_eur',
  'helsinki_benefit_total_eur',
];

export const CALCULATION_DESCRIPTION_ROW_TYPES = ['description'];

export const CALCULATION_TOTAL_ROW_TYPE = 'helsinki_benefit_total_eur';

export enum CALCULATION_TYPES {
  SALARY = 'salary',
  EMPLOYMENT = 'employment',
}

export const HANDLED_STATUSES: APPLICATION_STATUSES[] = [
  APPLICATION_STATUSES.ACCEPTED,
  APPLICATION_STATUSES.REJECTED,
  APPLICATION_STATUSES.CANCELLED,
];

export const DE_MINIMIS_AID_GRANTED_AT_MAX_DATE = new Date();

export const APPLICATION_START_DATE = new Date(new Date().getFullYear(), 0, 1);

export const MAX_DEMINIMIS_AID_TOTAL_AMOUNT = 200_000;

export const EMPLOYEE_MIN_WORKING_HOURS = 18;
export const EMPLOYEE_MAX_WORKING_HOURS = 168;

export const MAX_SHORT_STRING_LENGTH = 64 as const;
export const MAX_LONG_STRING_LENGTH = 256 as const;

export const MIN_PHONE_NUMBER_LENGTH = 3 as const;
export const MAX_PHONE_NUMBER_LENGTH = 13 as const;

export const EMPLOYEE_CONSENT_FILE_PREFIX = 'employee_consent';

export const DEFAULT_APPLICATION_STEP = 'step_1' as const;

export enum APPLICATION_FIELD_KEYS {
  USE_ALTERNATIVE_ADDRESS = 'useAlternativeAddress',
  ALTERNATIVE_COMPANY_STREET_ADDRESS = 'alternativeCompanyStreetAddress',
  ALTERNATIVE_COMPANY_POSTCODE = 'alternativeCompanyPostcode',
  ALTERNATIVE_COMPANY_CITY = 'alternativeCompanyCity',
  COMPANY_DEPARTMENT = 'companyDepartment',
  COMPANY_BANK_ACCOUNT_NUMBER = 'companyBankAccountNumber',
  ASSOCIATION_HAS_BUSINESS_ACTIVITIES = 'associationHasBusinessActivities',
  ASSOCIATION_IMMEDIATE_MANAGER_CHECK = 'associationImmediateManagerCheck',
  COMPANY_CONTACT_PERSON_FIRST_NAME = 'companyContactPersonFirstName',
  COMPANY_CONTACT_PERSON_LAST_NAME = 'companyContactPersonLastName',
  COMPANY_CONTACT_PERSON_PHONE_NUMBER = 'companyContactPersonPhoneNumber',
  COMPANY_CONTACT_PERSON_EMAIL = 'companyContactPersonEmail',
  APPLICANT_LANGUAGE = 'applicantLanguage',
  DE_MINIMIS_AID = 'deMinimisAid',
  DE_MINIMIS_AID_SET = 'deMinimisAidSet',
  CO_OPERATION_NEGOTIATIONS = 'coOperationNegotiations',
  CO_OPERATION_NEGOTIATIONS_DESCRIPTION = 'coOperationNegotiationsDescription',
  // ORGANIZATION_TYPE = 'organizationType',
  PAY_SUBSIDY_GRANTED = 'paySubsidyGranted',
  PAY_SUBSIDY_PERCENT = 'paySubsidyPercent',
  ADDITIONAL_PAY_SUBSIDY_PERCENT = 'additionalPaySubsidyPercent',
  APPRENTICESHIP_PROGRAM = 'apprenticeshipProgram',
  BENEFIT_TYPE = 'benefitType',
  START_DATE = 'startDate',
  END_DATE = 'endDate',
  EMPLOYEE = 'employee',
  APPLICANT_AGREEMENT = 'applicantAgreement',
  EMPLOYER_SIGNED = 'employerSigned',
  EMPLOYEE_SIGNED = 'employeeSigned',
  APPLICATION_ORIGIN = 'applicationOrigin',
}

export const APPLICATION_FIELDS = {
  ...APPLICATION_FIELD_KEYS,
  [APPLICATION_FIELD_KEYS.EMPLOYEE]: { ...EMPLOYEE_KEYS },
} as const;

export const APPLICATION_INITIAL_VALUES = {
  status: APPLICATION_STATUSES.DRAFT,
  employee: {
    [APPLICATION_FIELDS.employee.FIRST_NAME]: '',
    [APPLICATION_FIELDS.employee.LAST_NAME]: '',
    [APPLICATION_FIELDS.employee.PHONE_NUMBER]: '',
    [APPLICATION_FIELDS.employee.SOCIAL_SECURITY_NUMBER]: '',
    [APPLICATION_FIELDS.employee.JOB_TITLE]: '',
    [APPLICATION_FIELDS.employee.WORKING_HOURS]: '' as const,
    [APPLICATION_FIELDS.employee.COLLECTIVE_BARGAINING_AGREEMENT]: '',
    [APPLICATION_FIELDS.employee.MONTHLY_PAY]: '' as const,
    [APPLICATION_FIELDS.employee.OTHER_EXPENSES]: '' as const,
    [APPLICATION_FIELDS.employee.VACATION_MONEY]: '' as const,
    [APPLICATION_FIELDS.employee.COMMISSION_DESCRIPTION]: '',
    [APPLICATION_FIELDS.employee.EMPLOYEE_COMMISSION_AMOUNT]: '' as const,
  },
  bases: [],
  [APPLICATION_FIELD_KEYS.USE_ALTERNATIVE_ADDRESS]: false,
  [APPLICATION_FIELD_KEYS.ALTERNATIVE_COMPANY_STREET_ADDRESS]: '',
  [APPLICATION_FIELD_KEYS.ALTERNATIVE_COMPANY_CITY]: '',
  [APPLICATION_FIELD_KEYS.ALTERNATIVE_COMPANY_POSTCODE]: '',
  [APPLICATION_FIELD_KEYS.COMPANY_BANK_ACCOUNT_NUMBER]: '',
  [APPLICATION_FIELD_KEYS.COMPANY_CONTACT_PERSON_FIRST_NAME]: '',
  [APPLICATION_FIELD_KEYS.COMPANY_CONTACT_PERSON_LAST_NAME]: '',
  [APPLICATION_FIELD_KEYS.COMPANY_CONTACT_PERSON_PHONE_NUMBER]: '',
  [APPLICATION_FIELD_KEYS.COMPANY_CONTACT_PERSON_EMAIL]: '',
  [APPLICATION_FIELD_KEYS.APPLICANT_LANGUAGE]: SUPPORTED_LANGUAGES.FI,
  [APPLICATION_FIELD_KEYS.CO_OPERATION_NEGOTIATIONS]: null,
  [APPLICATION_FIELD_KEYS.CO_OPERATION_NEGOTIATIONS_DESCRIPTION]: '',
  [APPLICATION_FIELD_KEYS.DE_MINIMIS_AID]: null,
  [APPLICATION_FIELD_KEYS.DE_MINIMIS_AID_SET]: [],
  [APPLICATION_FIELD_KEYS.PAY_SUBSIDY_GRANTED]: null,
  [APPLICATION_FIELD_KEYS.PAY_SUBSIDY_PERCENT]: null,
  [APPLICATION_FIELD_KEYS.ADDITIONAL_PAY_SUBSIDY_PERCENT]: null,
  [APPLICATION_FIELD_KEYS.APPRENTICESHIP_PROGRAM]: null,
  archived: false,
  [APPLICATION_FIELD_KEYS.BENEFIT_TYPE]: '' as const,
  [APPLICATION_FIELD_KEYS.START_DATE]: '',
  [APPLICATION_FIELD_KEYS.END_DATE]: '',
  applicationStep: DEFAULT_APPLICATION_STEP,
  [APPLICATION_FIELD_KEYS.APPLICATION_ORIGIN]: APPLICATION_ORIGINS.HANDLER,
};

export const ALL_APPLICATION_STATUSES: APPLICATION_STATUSES[] = [
  APPLICATION_STATUSES.RECEIVED,
  APPLICATION_STATUSES.HANDLING,
  APPLICATION_STATUSES.INFO_REQUIRED,
  APPLICATION_STATUSES.ACCEPTED,
  APPLICATION_STATUSES.DRAFT,
  APPLICATION_STATUSES.REJECTED,
];
