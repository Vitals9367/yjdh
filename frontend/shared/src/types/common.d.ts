import React from 'react';

export type OptionType = {
  label: string;
  value: string | number;
};

export type NavigationItem = {
  label: string;
  url: string;
  icon?: React.ReactNode;
};

export type Headers = {
  [name: string]: string;
};
