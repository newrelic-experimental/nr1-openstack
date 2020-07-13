/* eslint-disable no-nested-ternary */
import React from 'react';
import PropTypes from 'prop-types';

import { Icon, Tooltip } from 'nr1';

import InfraStats from './infra-stats';

export default class HypervisorBoard extends React.Component {
  static propTypes = {
    hypervisors: PropTypes.object,
    hosts: PropTypes.object,
    openLink: PropTypes.func
  };

  render() {
    const { hypervisors, hosts, openLink } = this.props;

    const appIcon = (alertSeverity, reporting) =>
      reporting ? (
        alertSeverity === 'CRITICAL' ? (
          <Icon
            type={
              Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_ERROR
            }
            color="#bf0016"
          />
        ) : alertSeverity === 'WARNING' ? (
          <Icon
            type={
              Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_WARNING
            }
            color="#ffd966"
          />
        ) : (
          <Icon
            type={Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_OK}
            color="#11a600"
          />
        )
      ) : (
        <Icon
          type={
            Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_DISABLED
          }
          color="#ccc"
        />
      );

    const blockColor = (alertSeverity, reporting) =>
      reporting
        ? alertSeverity === 'CRITICAL'
          ? 'red'
          : alertSeverity === 'WARNING'
          ? 'yellow'
          : 'green'
        : 'grey';

    return (
      <div className="board">
        <h2>Hypervisors</h2>
        <div className="legend">
          <span className="icon">
            <Icon
              type={Icon.TYPE.HARDWARE_AND_SOFTWARE__KUBERNETES__K8S_CONTAINER}
            />
          </span>
          <span className="text">Hypervisor</span>
          <span className="icon">
            <Icon type={Icon.TYPE.HARDWARE_AND_SOFTWARE__KUBERNETES__K8S_POD} />
          </span>
          <span className="text">Server</span>
          <span className="icon">
            <Icon
              type={Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION}
            />
          </span>
          <span className="text">App</span>
        </div>
        {hypervisors &&
          Object.keys(hypervisors).map(hypervisor => (
            <div className="card parent" key={hypervisor}>
              <div className="header">
                <div className="type">
                  <Icon
                    type={
                      Icon.TYPE.HARDWARE_AND_SOFTWARE__KUBERNETES__K8S_CONTAINER
                    }
                  />
                </div>
                <div className="title">
                  {hypervisors[hypervisor].host}
                  &nbsp;[{hypervisors[hypervisor].name}]
                  <Tooltip
                    text={hypervisors[hypervisor].alertSeverity || 'unknown'}
                    placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
                  >
                    <span
                      className={`circle ${blockColor(
                        hypervisors[hypervisor].alertSeverity,
                        hypervisors[hypervisor].reporting
                      )}`}
                    />
                  </Tooltip>
                </div>
                <div className="meta" />
              </div>
              {hypervisors[hypervisor].servers.map(server => (
                <div className="card child" key={server.name}>
                  <div className="header">
                    <div className="type">
                      <Icon
                        type={
                          Icon.TYPE.HARDWARE_AND_SOFTWARE__KUBERNETES__K8S_POD
                        }
                      />
                    </div>
                    <div className="title">
                      {server.name}
                      <Tooltip
                        text={server.alertSeverity || 'unknown'}
                        placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
                      >
                        <span
                          className={`circle ${blockColor(
                            server.alertSeverity,
                            server.reporting
                          )}`}
                        />
                      </Tooltip>
                    </div>
                    <div className="blocks">
                      {server.apps.length > 0 &&
                        server.apps.map(app => (
                          <Tooltip
                            key={app.guid}
                            text={app.name}
                            placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
                          >
                            <div
                              className="cell app"
                              onClick={() => openLink(app.guid, 'entity')}
                            >
                              {appIcon(app.alertSeverity, app.reporting)}
                            </div>
                          </Tooltip>
                        ))}
                    </div>
                  </div>
                </div>
              ))}
              {hosts && hypervisors[hypervisor].host in hosts && (
                <InfraStats
                  data={hosts[hypervisors[hypervisor].host]}
                  host={hypervisors[hypervisor].host}
                  openLink={openLink}
                />
              )}
            </div>
          ))}
      </div>
    );
  }
}
