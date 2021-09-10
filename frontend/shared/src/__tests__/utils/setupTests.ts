import '@testing-library/jest-dom';

import { toHaveNoViolations } from 'jest-axe';
import JEST_TIMEOUT from 'shared/__tests__/utils/jest-timeout';

jest.setTimeout(JEST_TIMEOUT);

expect.extend(toHaveNoViolations);

// hide initReactI18next warning
// eslint-disable-next-line no-console
const originalError = console.error;
let consoleSpy: jest.SpyInstance;
beforeAll(() => {
  consoleSpy = jest.spyOn(console, 'warn').mockImplementation((...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes(
        'react-i18next:: You will need to pass in an i18next instance by using initReactI18next'
      )
    ) {
      return () => {};
    }
    return originalError.call(console, args);
  });
});

afterAll(() => {
  consoleSpy.mockRestore();
});