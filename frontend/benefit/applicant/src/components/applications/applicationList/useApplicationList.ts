import { ROUTES } from 'benefit/applicant/constants';
import FrontPageContext from 'benefit/applicant/context/FrontPageContext';
import useApplicationsQuery from 'benefit/applicant/hooks/useApplicationsQuery';
import { useTranslation } from 'benefit/applicant/i18n';
import { APPLICATION_STATUSES } from 'benefit-shared/constants';
import {
  ApplicationAllowedAction,
  ApplicationListItemData,
} from 'benefit-shared/types/application';
import { IconPen } from 'hds-react';
import camelCase from 'lodash/camelCase';
import { useRouter } from 'next/router';
import React, { useEffect } from 'react';
import isServerSide from 'shared/server/is-server-side';
import {
  convertToUIDateAndTimeFormat,
  convertToUIDateFormat,
} from 'shared/utils/date.utils';
import { getInitials } from 'shared/utils/string.utils';
import { DefaultTheme } from 'styled-components';

const translationListBase = 'common:applications.list';
const translationStatusBase = 'common:applications.statuses';

interface ApplicationListProps {
  list: ApplicationListItemData[];
  shouldShowSkeleton: boolean;
  shouldHideList: boolean;
}

const getAvatarBGColor = (
  status: APPLICATION_STATUSES
): keyof DefaultTheme['colors'] => {
  switch (status) {
    case APPLICATION_STATUSES.DRAFT:
      return 'black40';

    case APPLICATION_STATUSES.INFO_REQUIRED:
      return 'alert';

    case APPLICATION_STATUSES.RECEIVED:
      return 'info';

    case APPLICATION_STATUSES.APPROVED:
      return 'success';

    case APPLICATION_STATUSES.REJECTED:
      return 'error';

    default:
      return 'black40';
  }
};

const getEmployeeFullName = (firstName: string, lastName: string): string => {
  const name = `${firstName || ''} ${lastName || ''}`;
  return name === ' ' ? '-' : name;
};

const getOrderBy = (status: string[]): string =>
  status.includes('draft') ? '-modified_at' : '-submitted_at';

const useApplicationList = (status: string[]): ApplicationListProps => {
  const { t } = useTranslation();
  const router = useRouter();
  const orderBy = getOrderBy(status);
  const { data, error, isLoading } = useApplicationsQuery(status, orderBy);
  const { errors, setError } = React.useContext(FrontPageContext);

  useEffect(() => {
    if (error && !errors.includes(error)) {
      setError(error);
    }
  }, [errors, error, setError]);

  const getStatusTranslation = (
    applicationStatus: APPLICATION_STATUSES
  ): string => t(`${translationStatusBase}.${camelCase(applicationStatus)}`);

  const getAllowedActions = (
    id: string,
    applicationStatus: APPLICATION_STATUSES
  ): ApplicationAllowedAction => {
    const handleAction = (openDrawer: boolean): void => {
      void router.push(
        `${ROUTES.APPLICATION_FORM}?id=${id}${
          openDrawer ? '&openDrawer=1' : ''
        }`
      );
    };

    switch (applicationStatus) {
      case APPLICATION_STATUSES.DRAFT:
      case APPLICATION_STATUSES.INFO_REQUIRED:
        return {
          label: t(`${translationListBase}.common.edit`),
          handleAction,
          Icon: IconPen,
        };

      default:
        return {
          label: t(`${translationListBase}.common.check`),
          handleAction,
        };
    }
  };

  const list = data?.reduce<ApplicationListItemData[]>((acc, application) => {
    const {
      id = '',
      status: appStatus,
      employee,
      modified_at,
      submitted_at,
      application_number: applicationNum,
      additional_information_needed_by,
      unread_messages_count,
      batch,
    } = application;

    const statusText = getStatusTranslation(appStatus);
    const name = getEmployeeFullName(employee?.first_name, employee?.last_name);

    const avatar = {
      color: getAvatarBGColor(appStatus),
      initials: getInitials(name),
    };
    const allowedAction = getAllowedActions(id, appStatus);
    const submittedAt = submitted_at
      ? convertToUIDateFormat(submitted_at)
      : '-';
    const modifiedAtWithTime =
      modified_at && convertToUIDateAndTimeFormat(modified_at);
    const modifiedAt = modified_at && convertToUIDateFormat(modified_at);
    const editEndDate =
      additional_information_needed_by &&
      convertToUIDateFormat(additional_information_needed_by);
    const commonProps = {
      id,
      name,
      avatar,
      modifiedAt,
      allowedAction,
      status: appStatus,
      unreadMessagesCount: unread_messages_count ?? 0,
      batch,
    };
    const draftProps = { modifiedAt: modifiedAtWithTime, applicationNum };
    const submittedProps = {
      submittedAt,
      applicationNum,
      statusText,
    };
    const infoNeededProps = {
      submittedAt,
      applicationNum,
      editEndDate,
    };

    if (appStatus === APPLICATION_STATUSES.DRAFT) {
      const newDraftProps = { ...commonProps, ...draftProps };
      return [...acc, newDraftProps];
    }
    if (appStatus === APPLICATION_STATUSES.INFO_REQUIRED) {
      const newInfoNeededProps = { ...commonProps, ...infoNeededProps };
      return [...acc, newInfoNeededProps];
    }
    const newSubmittedProps = { ...commonProps, ...submittedProps };
    return [...acc, newSubmittedProps];
  }, []);

  const shouldShowSkeleton = !isServerSide() && isLoading;

  const shouldHideList =
    !shouldShowSkeleton && Array.isArray(data) && data.length === 0;

  return {
    list: list || [],
    shouldShowSkeleton,
    shouldHideList,
  };
};

export default useApplicationList;
