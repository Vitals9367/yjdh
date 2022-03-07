const { join } = require('path');

module.exports = {
  extends: ['auto', 'plugin:@next/next/recommended'],
  rules: {
    'no-secrets/no-secrets': ['error', { tolerance: 4.2 }],
    'sonarjs/cognitive-complexity': ['error', 20],
    'no-void': 'off',
    'unicorn/prefer-module': 'off',
    'jsx-a11y/anchor-is-valid': [
      'error',
      {
        components: ['Link'],
        specialLink: ['hrefLeft', 'hrefRight'],
        aspects: ['invalidHref', 'preferButton'],
      },
    ],
    'import/no-extraneous-dependencies': [
      'error',
      // Use package.json from both this package folder and root.
      { packageDir: [__dirname, join(__dirname, '../../')] },
    ],
    'unicorn/no-array-reduce': 'off',
    'unicorn/prefer-export-from': 'off',
    'react/jsx-pascal-case': ['error', { ignore: ['$*'] }],
    'react/function-component-definition': 'off',
    'sonarjs/no-nested-template-literals': 'off',
    'unicorn/prefer-node-protocol': 'off',
  },
  overrides: [
    {
      files: ['*.ts'],
      rules: {
        'import/prefer-default-export': 'off',
      },
    },
    {
      files: ['**/__tests__/**', '*.testcafe.ts'],
      rules: {
        'testing-library/render-result-naming-convention': 'off',
        'jest/expect-expect': 'off',
        'jest/no-done-callback': 'off',
      },
    },
    {
      files: ['*.components.ts'],
      rules: {
        'security/detect-non-literal-fs-filename': 'off',
      },
    },
  ],
};