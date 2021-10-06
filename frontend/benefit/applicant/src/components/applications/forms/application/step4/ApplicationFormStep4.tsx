import { ATTACHMENT_TYPES, BENEFIT_TYPES } from 'benefit/applicant/constants';
import { DynamicFormStepComponentProps } from 'benefit/applicant/types/common';
import { Button, IconPen } from 'hds-react';
import React, { useEffect } from 'react';
import FormSection from 'shared/components/forms/section/FormSection';

import StepperActions from '../stepperActions/StepperActions';
import AttachmentsListView from './attachmentsListView/AttachmentsListView';
import CompanyInfoView from './companyInfoView/CompanyInfoView';
import EmployeeView from './employeeView/EmployeeView';
import { useApplicationFormStep4 } from './useApplicationFormStep4';

const ApplicationFormStep4: React.FC<DynamicFormStepComponentProps> = ({
  data,
}) => {
  const {
    t,
    handleBack,
    handleNext,
    handleSave,
    handleStepChange,
    translationsBase,
  } = useApplicationFormStep4(data);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <>
      <CompanyInfoView data={data} handleStepChange={handleStepChange} />

      <EmployeeView data={data} handleStepChange={handleStepChange} />

      <FormSection
        header={t(`${translationsBase}.attachments.heading1`)}
        action={
          <Button
            theme="black"
            onClick={() => handleStepChange(3)}
            variant="supplementary"
            iconLeft={<IconPen />}
          >
            {t(`common:applications.actions.edit`)}
          </Button>
        }
      >
        <>
          {(data.benefitType === BENEFIT_TYPES.EMPLOYMENT ||
            data.benefitType === BENEFIT_TYPES.SALARY) && (
            <>
              <AttachmentsListView
                type={ATTACHMENT_TYPES.EMPLOYMENT_CONTRACT}
                title={t(
                  `${translationsBase}.attachments.types.employmentContract.title`
                )}
                attachments={data.attachments || []}
              />
              <AttachmentsListView
                type={ATTACHMENT_TYPES.PAY_SUBSIDY_CONTRACT}
                title={t(
                  `${translationsBase}.attachments.types.paySubsidyDecision.title`
                )}
                attachments={data.attachments || []}
              />
              <AttachmentsListView
                type={ATTACHMENT_TYPES.EDUCATION_CONTRACT}
                title={t(
                  `${translationsBase}.attachments.types.educationContract.title`
                )}
                attachments={data.attachments || []}
              />
            </>
          )}
        </>
        {data.benefitType === BENEFIT_TYPES.COMMISSION && (
          <AttachmentsListView
            type={ATTACHMENT_TYPES.COMMISSION_CONTRACT}
            title={t(
              `${translationsBase}.attachments.types.commissionContract.title`
            )}
            attachments={data.attachments || []}
          />
        )}
        <AttachmentsListView
          type={ATTACHMENT_TYPES.HELSINKI_BENEFIT_VOUCHER}
          title={t(
            `${translationsBase}.attachments.types.helsinkiBenefitVoucher.title`
          )}
          attachments={data.attachments || []}
        />
      </FormSection>

      <StepperActions
        handleSubmit={handleNext}
        handleSave={handleSave}
        handleBack={handleBack}
      />
    </>
  );
};

export default ApplicationFormStep4;
