import { BackendEndpoint } from 'benefit-shared/backend-api/backend-api';
import { User, UserData } from 'benefit-shared/types/application';
import camelcaseKeys from 'camelcase-keys';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { useQuery, UseQueryResult } from 'react-query';
import showErrorToast from 'shared/components/toast/show-error-toast';
import useBackendAPI from 'shared/hooks/useBackendAPI';
import useLocale from 'shared/hooks/useLocale';
import {
  getLocalStorageItem,
  setLocalStorageItem,
} from 'shared/utils/localstorage.utils';

import { LOCAL_STORAGE_KEYS } from '../constants';

// check that authentication is still alive in every 5 minutes
const FIVE_MINUTES = 5 * 60 * 1000;

const UNAUTHORIZER_ROUTES = new Set(['/login', '/accessibility-statement']);

const useUserQuery = (
  queryKeys?: string | unknown[]
): UseQueryResult<User, Error> => {
  const { t } = useTranslation();
  const router = useRouter();
  const logout =
    router.route === '/login' && router.asPath.includes('logout=true'); // router.query doesn't always contain the logout parameter
  const locale = useLocale();
  const { axios, handleResponse } = useBackendAPI();

  const handleError = (error: Error): void => {
    if (logout) {
      void router.push(`${locale}/login?logout=true`);
    } else if (/40[13]/.test(error.message)) {
      if (UNAUTHORIZER_ROUTES.has(router.route)) {
        return;
      }
      void router.push(`${locale}/login`);
    } else {
      showErrorToast(
        t('common:error.generic.label'),
        t('common:error.generic.text')
      );
    }
  };

  const params =
    getLocalStorageItem(LOCAL_STORAGE_KEYS.IS_TERMS_OF_SERVICE_APPROVED) ===
    'true'
      ? {}
      : { terms: 1 };

  return useQuery(
    queryKeys ?? `${BackendEndpoint.USER}`,
    () =>
      handleResponse<UserData>(axios.get(BackendEndpoint.USER_ME, { params })),
    {
      refetchInterval: FIVE_MINUTES,
      enabled: !logout,
      retry: false,
      select: (data) => camelcaseKeys(data, { deep: true }),
      onError: (error) => handleError(error),
      onSuccess: (data) => {
        const { id, csrfToken, termsOfServiceApprovalNeeded } = data;
        setLocalStorageItem(LOCAL_STORAGE_KEYS.CSRF_TOKEN, csrfToken);
        axios.defaults.headers['X-CSRFToken'] = csrfToken;
        if (id && termsOfServiceApprovalNeeded)
          setLocalStorageItem(
            LOCAL_STORAGE_KEYS.IS_TERMS_OF_SERVICE_APPROVED,
            'false'
          );
      },
    }
  );
};
export default useUserQuery;
