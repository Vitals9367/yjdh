import { Notification as HDSNotification } from 'hds-react';
import { $FormGroup } from 'shared/components/forms/section/FormSection.sc';
import styled from 'styled-components';

export const $CompanyInfoContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-areas:
    'info info notification notification'
    'address address address address'
    'iban iban iban iban';
  width: 100%;
  grid-gap: 0 ${(props) => props.theme.spacing.xs};
`;

export const $CompanyInfoSection = styled.div`
  grid-area: info;
  display: flex;
  flex-wrap: wrap;
`;

export const $CompanyInfoColumn = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1 0 50%;
`;

export const $CompanyInfoRow = styled.div`
  display: flex;
  line-height: ${(props) => props.theme.lineHeight.l};
  height: ${(props) => `calc(${props.theme.lineHeight.l} * 1em)`};
  margin-right: ${(props) => props.theme.spacing.l};
  margin-bottom: ${(props) => props.theme.spacing.xs2};
`;

export const $Notification = styled(HDSNotification)`
  grid-area: notification;
  font-size: ${(props) => props.theme.fontSize.heading.xs};
`;

export const $AddressContainer = styled($FormGroup)`
  grid-area: address;
  margin-top: ${(props) => props.theme.spacing.l};
  display: grid;
  align-items: baseline;
  grid-template-columns: 4fr 2fr 4fr 2fr;
  grid-gap: ${(props) => props.theme.spacing.xs};
`;

export const $IBANContainer = styled($FormGroup)`
  grid-area: iban;
  margin-top: ${(props) => props.theme.spacing.xl};
  display: grid;
  grid-template-columns: 3fr 9fr;
`;