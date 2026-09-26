import React from 'react';
import { createRoot } from 'react-dom/client';
import { Sidebar, Example, type DashboardData } from '../components/ui/dashboard-with-collapsible-sidebar';
const sidebar = document.getElementById('admin-sidebar-root');
if (sidebar?.dataset.dashboard) {
  const data: DashboardData = JSON.parse(sidebar.dataset.dashboard);
  createRoot(sidebar).render(<Sidebar data={data}/>);
  const overview = document.getElementById('admin-overview-root');
  if (overview) createRoot(overview).render(<Example data={data}/>);
}
