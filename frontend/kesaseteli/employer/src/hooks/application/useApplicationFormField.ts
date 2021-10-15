import useGetApplicationFormFieldLabel from 'kesaseteli/employer/hooks/application/useGetApplicationFormFieldLabel';
import { useTranslation } from 'next-i18next';
import React from 'react';
import {
  ErrorOption,
  FieldError,
  get,
  useFormContext,
  UseFormRegister,
} from 'react-hook-form';
import ApplicationFieldName from 'shared/types/application-field-name';
import Application from 'shared/types/application-form-data';
import Employment from 'shared/types/employment';
import { getLastValue } from 'shared/utils/array.utils';
import {
  convertToUIDateFormat,
  isDateObject,
  parseDate,
} from 'shared/utils/date.utils';

type Value =
  | Application[keyof Application]
  | Employment
  | Employment[keyof Employment];

type ApplicationFormField<V extends Value> = {
  fieldName: ApplicationFieldName;
  defaultLabel: string;
  getValue: () => V;
  watch: () => V;
  setValue: (value: V) => void;
  getError: () => FieldError | undefined;
  hasError: () => boolean;
  getErrorText: () => string | undefined;
  setError: (type: ErrorOption['type']) => void;
  clearValue: () => void;
  trigger: () => Promise<boolean>;
  clearErrors: () => void;
  getSummaryText: () => string;
};

const useApplicationFormField = <V extends Value>(
  id: NonNullable<Parameters<UseFormRegister<Application>>[0]>
): ApplicationFormField<V> => {
  const { t } = useTranslation();
  const {
    getValues,
    setValue,
    watch,
    trigger,
    clearErrors,
    formState,
    setError: setErrorF,
  } = useFormContext<Application>();
  const fieldName = (getLastValue((id as string).split('.')) ??
    '') as ApplicationFieldName;
  const defaultLabel = useGetApplicationFormFieldLabel(fieldName);

  const getValue = React.useCallback((): V => {
    const value = getValues(id) as string;
    if (isDateObject(parseDate(value))) {
      return convertToUIDateFormat(value) as V;
    }
    return value as V;
  }, [getValues, id]);

  const setValueF = React.useCallback(
    (value: V) => setValue(id, value),
    [setValue, id]
  );
  const watchF = React.useCallback(() => watch(id) as V, [watch, id]);
  const getError = React.useCallback(
    (): FieldError | undefined =>
      get(formState.errors, id) as FieldError | undefined,
    [formState, id]
  );
  const hasError = React.useCallback(() => Boolean(getError()), [getError]);

  const setError = React.useCallback(
    (type: ErrorOption['type']) => setErrorF(id, { type }),
    [id, setErrorF]
  );

  const getErrorText = React.useCallback((): string | undefined => {
    const type = getError()?.type as string;
    return type ? t(`common:application.form.errors.${type}`) : undefined;
  }, [getError, t]);

  const clearValue = React.useCallback(() => setValue(id, ''), [setValue, id]);
  const triggerF = React.useCallback(
    () => trigger(id, { shouldFocus: true }),
    [trigger, id]
  );
  const clearErrorsF = React.useCallback(
    () => clearErrors(id),
    [clearErrors, id]
  );
  const getSummaryText = React.useCallback(() => {
    const value = getValue();
    return `${defaultLabel}: ${value ? value.toString() : '-'}`;
  }, [getValue, defaultLabel]);

  return React.useMemo(
    () => ({
      fieldName,
      defaultLabel,
      getValue,
      setValue: setValueF,
      watch: watchF,
      getError,
      hasError,
      getErrorText,
      setError,
      clearValue,
      trigger: triggerF,
      clearErrors: clearErrorsF,
      getSummaryText,
    }),
    [
      fieldName,
      defaultLabel,
      getValue,
      setValueF,
      watchF,
      getError,
      hasError,
      getErrorText,
      setError,
      clearValue,
      triggerF,
      clearErrorsF,
      getSummaryText,
    ]
  );
};
export default useApplicationFormField;
