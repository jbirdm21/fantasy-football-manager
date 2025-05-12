
import React from 'react';

/**
 * Dashboard test component for task: Draft analytics dashboard
 * Task ID: task-04a530c6-d265-4ad0-a510-1e5df74c62f1
 */
export const TestDashboardComponent = () => {
  return (
    <div className="dashboard-container">
      <h2>Dashboard Test</h2>
      <p>This component was created for task: Draft analytics dashboard</p>
      <div className="metrics-panel">
        <div className="metric">
          <h3>Total Points</h3>
          <p className="value">128.5</p>
        </div>
        <div className="metric">
          <h3>Win Probability</h3>
          <p className="value">68%</p>
        </div>
      </div>
    </div>
  );
};
