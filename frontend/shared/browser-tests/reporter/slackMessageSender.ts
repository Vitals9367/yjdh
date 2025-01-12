import Slack, { WebhookOptions, WebhookResponse } from 'slack-node';

import { bold, codeBlock } from './utils/slackTextFormatters';

type SlackMessageSender = {
  addMessage: (message: string) => void;
  addErrorMessage: (message: string) => void;
  sendMessage: (message: string, slackProperties?: WebhookOptions) => void;
  sendTestReport: (amountOfFailedTests: number) => void;
};

/**
 * Based on https://www.charactercountonline.com/ it seems that slack message accepts maximum of 7200 characters
 */
const SLACK_MESSAGE_MAX_LENGTH = 7200;

export const createSlackMessageSender = (): SlackMessageSender => {
  const slack = new Slack();
  slack.setWebhook(process.env.TESTCAFE_SLACK_WEBHOOK || '');
  const channel = process.env.TESTCAFE_SLACK_CHANNEL;
  const username = process.env.TESTCAFE_SLACK_USERNAME;
  const messages: string[] = [];
  const errorMessages: string[] = [];

  const addMessage = (message: string): void => {
    messages.push(message);
  };

  const addErrorMessage = (errorMessage: string): void => {
    // error message length might exceed max limit of slack message. Minus six (-6) is because of codeBlock size.
    const msg = errorMessage.slice(
      0,
      Math.max(0, SLACK_MESSAGE_MAX_LENGTH - 6)
    );
    errorMessages.push(codeBlock(msg));
  };

  const sendMessage = (
    message: string,
    slackProperties: WebhookOptions = {}
  ): void => {
    slack.webhook(
      {
        channel,
        username,
        text: message,
        ...slackProperties,
      },
      (err: Error, response: WebhookResponse) => {
        if (err) {
          // eslint-disable-next-line no-console
          console.log('Unable to send a message to slack', response, err.stack);
        }
      }
    );
  };

  const sendTestReport = (amountOfFailedTests: number): void => {
    // send report only when something has failed
    const message = messages.join('\n');
    if (amountOfFailedTests > 0) {
      // eslint-disable-next-line no-console
      console.log('Slack message', message);
      if (process.env.TESTCAFE_SLACK_WEBHOOK) {
        sendMessage(
          message,
          amountOfFailedTests
            ? {
                attachments: [
                  ...errorMessages.map((msg) => ({
                    color: 'danger',
                    text: msg,
                  })),
                  {
                    color: 'danger',
                    text: bold(`${amountOfFailedTests} test failed!`),
                  },
                ],
              }
            : undefined
        );
      }
    }
  };

  return {
    addMessage,
    addErrorMessage,
    sendMessage,
    sendTestReport,
  };
};
