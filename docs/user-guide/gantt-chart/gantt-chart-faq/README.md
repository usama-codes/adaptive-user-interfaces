---
sidebar_navigation:
  title: Gantt chart FAQ
  priority: 001
description: Frequently asked questions regarding Gantt chart
keywords: Gantt chart FAQ, time line, scheduling
---

# Frequently asked questions (FAQ) for Gantt chart

## How can I move the milestones in the Gantt chart to a specific date, independently from the other work packages?

Make sure that you remove the relations of the milestone to other work packages. Then its date won't change when you change the timings of other work packages. For releases from 11.0.0 onwards (October 2020) you can use the [manual scheduling mode](../scheduling) for this.

## When I am working in the Gantt chart, every change seems to take quite long. What can I do?

We understand that the loading time when working in Gantt Chart is too long for you. The reason for this is that every single action is saved. So everything is fine with your installation. We have already taken up the point with us and already have first ideas for a technical solution. The respective feature request can be found [here](https://community.openproject.org/wp/34176).

## Can I export the Gantt?

Yes, you can. Please keep in mind that [PDF export of a Gantt chart](../#gantt-chart-pdf-export-enterprise-add-on) is an Enterprise add-on. 

You can also use the print feature of your browser to print it as PDF (we optimized this for Google Chrome). Please find out more [here](../#how-to-print-a-gantt-chart).

If you only want to export the data from the work packages included into the Gantt chart, you can use the [work package export feature](../../work-packages/exporting/). 

## I can no longer see my Gantt chart filters, what can I do?

Gantt charts became a separate module in OpenProject 13.3. To see the filters you created and saved earlier please select the **Gantt charts** module either from the global modules menu or from the project menu on the left.

## How can I build in a "buffer" (e.g. two weeks gap) between two consecutive work packages, so that even if the first one is postponed the second one always starts e.g. two weeks later?

You can do this by setting up **Predecessor/Successor** relation between the consecutive work packages and defining the respective lag. Read more about [work package relations](../../work-packages/work-package-relations-hierarchies/#work-package-relations).

## Is there a critical path feature?

Unfortunately, we don't have the critical path feature yet. We have a feature request for it though and will check how to integrate it into our road map. A workaround could be to [create predecessor-successor relations](../../work-packages/work-package-relations-hierarchies/#work-package-relations) for only the work packages that are in the critical path.
