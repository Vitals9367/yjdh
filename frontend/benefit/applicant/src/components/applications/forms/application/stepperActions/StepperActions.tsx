import { useTranslation } from 'benefit/applicant/i18n';
import { Button, IconArrowLeft, IconArrowRight, IconCross } from 'hds-react';
import noop from 'lodash/noop';
import * as React from 'react';
import {
  $Grid,
  $GridCell,
} from 'shared/components/forms/section/FormSection.sc';

type StepperActionsProps = {
  hasBack?: boolean;
  hasNext?: boolean;
  handleBack?: () => void;
  handleSubmit?: () => void;
};

const StepperActions: React.FC<StepperActionsProps> = ({
  hasBack,
  hasNext,
  handleBack,
  handleSubmit,
}: StepperActionsProps) => {
  const { t } = useTranslation();
  const translationsBase = 'common:applications.actions';
  return (
    <$Grid>
      <$GridCell $colSpan={2}>
        {hasBack && (
          <Button
            theme="black"
            variant="secondary"
            iconLeft={<IconArrowLeft />}
            onClick={handleBack}
            fullWidth
          >
            {t(`${translationsBase}.back`)}
          </Button>
        )}
      </$GridCell>
      <$GridCell $colSpan={8} justifySelf="center">
        <Button theme="black" variant="secondary" fullWidth>
          {t(`${translationsBase}.saveAndContinueLater`)}
        </Button>
      </$GridCell>
      <$GridCell $colSpan={2}>
        <Button
          theme="coat"
          iconRight={<IconArrowRight />}
          onClick={handleSubmit}
          fullWidth
        >
          {hasNext
            ? t(`${translationsBase}.continue`)
            : t(`${translationsBase}.send`)}
        </Button>
      </$GridCell>
      <$GridCell $colSpan={10} $colStart={2} justifySelf="center">
        <Button
          theme="black"
          variant="supplementary"
          iconLeft={<IconCross />}
          fullWidth
        >
          {t(`${translationsBase}.deleteApplication`)}
        </Button>
      </$GridCell>
    </$Grid>
  );
};

const defaultProps = {
  hasBack: false,
  hasNext: false,
  handleBack: noop,
  handleSubmit: noop,
};

StepperActions.defaultProps = defaultProps;

export default StepperActions;
