import { LoadingSpinner } from 'hds-react';
import React from 'react';

import { $SpinnerContainer } from './PageLoadingSpinner.sc';

const PageLoadingSpinner = (): JSX.Element => (
  <$SpinnerContainer data-testid="page-loading-spinner">
    <LoadingSpinner />
  </$SpinnerContainer>
);

export default PageLoadingSpinner;
