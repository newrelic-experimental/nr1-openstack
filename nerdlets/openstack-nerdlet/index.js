import React from 'react';

import { navigation, NerdGraphQuery } from 'nr1';

import HypervisorBoard from './hypervisor-board';
import DomainBoard from './domain-board';
import DashboardList from './dashboard-list';

import queries from './queries';
import parse from './parse';

export default class OpenstackNerdlet extends React.Component {
  state = {};

  componentDidMount() {
    this.fetchData();
  }

  fetchData = async () => {
    const res = await NerdGraphQuery.query({ query: queries.graphql });
    // console.log(res);

    const parsedData = parse.data(res);
    // eslint-disable-next-line no-console
    console.log(parsedData);

    this.setState(parsedData);
  };

  openLink = (link, type) => {
    if (type === 'entity') return navigation.openStackedEntity(link);
    if (type === 'nerdlet') return navigation.openStackedNerdlet(link);
  };

  render() {
    const {
      hypervisors,
      hosts,
      domains,
      dashboards,
      nova,
      keystone
    } = this.state;

    return (
      <div className="container">
        <div className="main">
          <DashboardList dashboards={dashboards} openLink={this.openLink} />
          <div className="boards">
            <HypervisorBoard
              hypervisors={hypervisors}
              hosts={hosts}
              openLink={this.openLink}
            />
            <DomainBoard
              domains={domains}
              nova={nova}
              keystone={keystone}
              openLink={this.openLink}
            />
          </div>
        </div>
      </div>
    );
  }
}
