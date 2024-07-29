import React from 'react';
import { Model } from 'survey-core';
import { Survey } from 'survey-react-ui';
import 'survey-core/defaultV2.min.css';

import { StylesManager } from 'survey-core';

StylesManager.applyTheme("defaultV2");

const customTheme = {
  cssVariables: {
    "--sjs-general-backcolor": "var(--background)",
    "--sjs-general-forecolor": "var(--foreground)",
    "--sjs-header-backcolor": "var(--background)",
    "--sjs-header-forecolor": "var(--foreground)",
    "--sjs-body-backcolor": "var(--background)",
    "--sjs-body-forecolor": "var(--foreground)",
    "--sjs-base-unit": "8px",
    "--sjs-corner-radius": "4px",
    "--sjs-secondary-backcolor": "var(--background-dim)",
    "--sjs-secondary-forecolor": "var(--foreground)",
    "--sjs-primary-backcolor": "var(--primary)",
    "--sjs-primary-forecolor": "var(--primary-foreground)",
  }
};

StylesManager.applyTheme(customTheme);
const surveyJson = {
  pages: [
    {
      name: "page1",
      elements: [
        {
          type: "text",
          name: "name",
          title: "Enter your name:"
        }
      ]
    },
    {
      name: "page2",
      elements: [
        {
          type: "text",
          name: "email",
          title: "Enter your email:"
        }
      ]
    }
  ]
};

export function SurveyComponent() {
  const survey = new Model(surveyJson);
  return <Survey model={survey} />;
}

