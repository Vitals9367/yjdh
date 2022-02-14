import TestController from 'testcafe';

import { getNotificationPageComponents } from './notificationPage.components';

export const getAlreadyActivatedPageComponents = async (t: TestController) =>
  getNotificationPageComponents(t, {
    headerText:
      /hups! olet jo aikaisemmin lähettänyt kesäsetelihakemuksen ja se on nyt käsittelyssä/i,
  });
