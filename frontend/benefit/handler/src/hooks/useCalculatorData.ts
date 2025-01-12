import { CALCULATION_TYPES } from 'benefit/handler/constants';
import { CalculationFormProps } from 'benefit/handler/types/application';
import { getErrorText } from 'benefit/handler/utils/forms';
import { FormikProps } from 'formik';
import { TFunction, useTranslation } from 'next-i18next';
import { useEffect, useState } from 'react';
import useLocale from 'shared/hooks/useLocale';
import { Language } from 'shared/i18n/i18n';
import { focusAndScroll } from 'shared/utils/dom.utils';
import { DefaultTheme, useTheme } from 'styled-components';

type ExtendedComponentProps = {
  t: TFunction;
  translationsBase: string;
  theme: DefaultTheme;
  language: Language;
  handleSubmit: () => void;
  handleClear: () => void;
  getErrorMessage: (fieldName: string) => string | undefined;
  isRecalculationRequired: boolean;
};

const useCalculatorData = (
  calculatorType: CALCULATION_TYPES,
  formik: FormikProps<CalculationFormProps>
): ExtendedComponentProps => {
  const language = useLocale();
  const theme = useTheme();
  const translationsBase = `common:calculators.${calculatorType}`;
  const { t } = useTranslation();

  const { errors, touched, values, dirty } = formik;

  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);

  const [isRecalculationRequired, setIsRecalculationRequired] = useState(false);

  const getErrorMessage = (fieldName: string): string | undefined =>
    getErrorText(errors, touched, fieldName, t, isSubmitted);

  const handleSubmit = (): void => {
    setIsSubmitted(true);
    void formik.validateForm().then((errs) => {
      const fieldName = Object.keys(errs)[0];
      if (!fieldName) {
        setIsRecalculationRequired(false);
        return formik.submitForm();
      }
      return focusAndScroll(fieldName);
    });
  };

  const handleClear = (): void => {
    formik.resetForm();
  };

  useEffect(() => {
    if (dirty) setIsRecalculationRequired(true);
  }, [dirty, values]);

  return {
    t,
    translationsBase,
    theme,
    language,
    getErrorMessage,
    handleSubmit,
    handleClear,
    isRecalculationRequired,
  };
};

export { useCalculatorData };
