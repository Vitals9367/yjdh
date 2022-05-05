import { getBackendDomain } from '@frontend/kesaseteli-shared/src/backend-api/backend-api';
import { HttpRequestHook } from '@frontend/shared/browser-tests/http-utils/http-request-hook';
import requestLogger, {
  filterLoggedRequests,
} from '@frontend/shared/browser-tests/utils/request-logger';
import { clearDataToPrintOnFailure } from '@frontend/shared/browser-tests/utils/testcafe.utils';

import getEmployerTranslationsApi from '../../src/__tests__/utils/i18n/get-employer-translations-api';
import { doEmployerLogin } from '../actions/employer-header.actions';
import { getFrontendUrl } from '../utils/url.utils';
import Header from 'shared/page-models/Header';

const url = getFrontendUrl('/');
let header: Header;
const translationsApi = getEmployerTranslationsApi();

fixture('Frontpage')
  .page(url)
  .requestHooks(requestLogger, new HttpRequestHook(url, getBackendDomain()))
  .beforeEach(async (t) => {
    clearDataToPrintOnFailure(t);
    header = new Header(translationsApi);
  })
  .afterEach(async () =>
    // eslint-disable-next-line no-console
    console.log(filterLoggedRequests(requestLogger))
  );

test('user can authenticate and logout', async (t) => {
  await doEmployerLogin(t, 'fi');
  await header.clickLogoutButton();
  await header.userIsLoggedOut();
});

test('can change to languages', async () => {
  await header.isLoaded();
  await header.changeLanguage('sv');
  const headerSv = new Header(translationsApi, 'sv');
  await headerSv.isLoaded();
  await headerSv.changeLanguage('en');
  const headerEn = new Header(translationsApi, 'en');
  await headerEn.isLoaded();
  await headerEn.changeLanguage('fi');
  await new Header(translationsApi, 'fi').isLoaded();
});
