/* eslint-disable no-nested-ternary */
import React from 'react';
import PropTypes from 'prop-types';

import { Icon, Tooltip } from 'nr1';

import DomainStats from './domain-stats';

export default class DomainBoard extends React.Component {
  static propTypes = {
    domains: PropTypes.object,
    nova: PropTypes.object,
    keystone: PropTypes.object,
    openLink: PropTypes.func
  };

  render() {
    const { domains, nova, keystone, openLink } = this.props;

    const appIcon = (alertSeverity, reporting, guid) => {
      const [type, color] = reporting
        ? alertSeverity === 'CRITICAL'
          ? [
              Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_ERROR,
              '#bf0016'
            ]
          : alertSeverity === 'WARNING'
          ? [
              Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_WARNING,
              '#ffd966'
            ]
          : [
              Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_OK,
              '#11a600'
            ]
        : [
            Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION__S_DISABLED,
            '#ccc'
          ];

      return (
        <span onClick={() => openLink(guid, 'entity')}>
          <Icon type={type} color={color} />
        </span>
      );
    };

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
        <h2>Domains/Projects</h2>
        <div className="legend">
          <span className="icon">
            <Icon type={Icon.TYPE.INTERFACE__OPERATIONS__ARCHIVE} />
          </span>
          <span className="text">Domain</span>
          <span className="icon">
            <Icon type={Icon.TYPE.DOCUMENTS__DOCUMENTS__FOLDER} />
          </span>
          <span className="text">Project</span>
          <span className="icon block round grey" />
          <span className="text">Server (no apps)</span>
          <span className="icon pill" />
          <span className="text">Server w/ apps</span>
          <span className="icon">
            <Icon
              type={Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__APPLICATION}
            />
          </span>
          <span className="text">App</span>
        </div>
        {domains &&
          Object.keys(domains).map(domain => (
            <div className="card parent" key={domain}>
              <div className="header">
                <div className="type">
                  <Icon type={Icon.TYPE.INTERFACE__OPERATIONS__ARCHIVE} />
                </div>
                <div className="title">{domain}</div>
                <div className="meta" />
              </div>
              {Object.keys(domains[domain]).map(project => (
                <div className="card child" key={project}>
                  <div className="header">
                    <div className="type">
                      <Icon type={Icon.TYPE.DOCUMENTS__DOCUMENTS__FOLDER} />
                    </div>
                    <div className="title">{project}</div>
                    <div className="meta" />
                  </div>
                  {domains[domain][project].length ? (
                    <div className="pills">
                      {domains[domain][project].map(server => (
                        <div
                          key={server.name}
                          className={`pill border-${blockColor(
                            server.alertSeverity,
                            server.reporting
                          )} ${server.apps.length < 1 ? 'no-apps' : ''}`}
                        >
                          <div className="block">
                            <Tooltip
                              key={server.name}
                              text={server.name}
                              placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
                            >
                              <div
                                className={`cell ${blockColor(
                                  server.alertSeverity,
                                  server.reporting
                                )}`}
                              />
                            </Tooltip>
                          </div>
                          {server.apps.length > 0 ? (
                            <div className="block child">
                              {server.apps.map(app => (
                                <Tooltip
                                  key={app.guid}
                                  text={app.name}
                                  placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
                                >
                                  {appIcon(
                                    app.alertSeverity,
                                    app.reporting,
                                    app.guid
                                  )}
                                </Tooltip>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
              <DomainStats
                data={nova && domain in nova ? nova[domain] : null}
                type="nova"
              />
              <DomainStats
                data={keystone && domain in keystone ? keystone[domain] : null}
                type="keystone"
              />
            </div>
          ))}
      </div>
    );
  }
}
