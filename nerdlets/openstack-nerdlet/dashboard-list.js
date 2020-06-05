import React from 'react';
import PropTypes from 'prop-types';

import { Dropdown, DropdownItem } from 'nr1';

export default class DashboardList extends React.Component {
  static propTypes = {
    dashboards: PropTypes.array,
    openLink: PropTypes.func
  };

  render() {
    const { dashboards, openLink } = this.props;

    return (
      <div className="menu-bar">
        {dashboards && (
          <Dropdown title="Other Dashboards" className="dashboard-list">
            {dashboards.map(dashboard => (
              <DropdownItem
                key={dashboard.guid}
                onClick={() => openLink(dashboard.guid, 'entity')}
              >
                {dashboard.name}
              </DropdownItem>
            ))}
          </Dropdown>
        )}
      </div>
    );
  }
}
