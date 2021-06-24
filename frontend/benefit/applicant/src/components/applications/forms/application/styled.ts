import { Button, TextInput, TextInputProps } from 'hds-react';
import React from 'react';
import styled from 'styled-components';

const StyledContainer = styled.div`
  display: flex;
  justify-content: space-between;
  padding-bottom: ${(props) => props.theme.spacing.m};
`;

const StyledTextContainer = styled.div`
  flex: 1 0 50%;
  box-sizing: border-box;
`;

const StyledHeading = styled.h1`
  font-size: ${(props) => props.theme.fontSize.heading.xl};
  font-weight: normal;
`;

const StyledDescription = styled.p`
  font-size: ${(props) => props.theme.fontSize.heading.s};
  font-weight: normal;
  line-height: ${(props) => props.theme.lineHeight.l};
`;

const StyledLink = styled.span`
  text-decoration: underline;
  cursor: pointer;
`;

const StyledActionContainer = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex: 1 0 50%;
  box-sizing: border-box;
`;

const StyledSubActionContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  align-self: stretch;
  justify-self: stretch;
  box-sizing: border-box;
  background-color: white;
  flex: 1 0 auto;
  margin-right: 0 !important;
`;

interface ButtonProps {
  icon?: React.ReactNode;
}

const StyledButton = styled(Button)<ButtonProps>`
  background-color: ${(props) => props.theme.colors.coatOfArms} !important;
  border-color: ${(props) => props.theme.colors.coatOfArms} !important;
`;

const StyledCompanyInfoContainer = styled.div`
  display: flex;
  width: 100%;
`;

const StyledCompanyInfoSection = styled.div`
  display: flex;
  flex: 1 0 50%;
`;

const StyledCompanyInfoColumn = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1 0 50%;
`;

const StyledCompanyInfoRow = styled.div`
  display: flex;
`;

const StyledNotificationContent = styled.div`
  font-size: ${(props) => props.theme.fontSize.heading.xs};
`;

const StyledSubSection = styled.div`
  margin-left: 200px;

  textarea {
    width: 640px !important;
  }
`;

const StyledIBANField = styled(TextInput)<TextInputProps>`
  input {
    width: 13.5em !important;
  }
`;

export {
  StyledActionContainer,
  StyledButton,
  StyledCompanyInfoColumn,
  StyledCompanyInfoContainer,
  StyledCompanyInfoRow,
  StyledCompanyInfoSection,
  StyledContainer,
  StyledDescription,
  StyledHeading,
  StyledIBANField,
  StyledLink,
  StyledNotificationContent,
  StyledSubActionContainer,
  StyledSubSection,
  StyledTextContainer,
};
