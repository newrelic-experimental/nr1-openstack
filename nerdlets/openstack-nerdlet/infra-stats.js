/* eslint-disable no-nested-ternary */
import React from 'react';
import PropTypes from 'prop-types';

import { Button, Tooltip } from 'nr1';

import num from '../../utils/number';

export default class InfraStats extends React.Component {
  static propTypes = {
    data: PropTypes.object,
    host: PropTypes.string,
    openLink: PropTypes.func
  };

  render() {
    const { data, host, openLink } = this.props;

    const blockColor = (alertSeverity, reporting) =>
      reporting
        ? alertSeverity === 'CRITICAL'
          ? 'red'
          : alertSeverity === 'WARNING'
          ? 'yellow'
          : 'green'
        : 'grey';

    return data ? (
      <div className="infra">
        <div className="title">
          <div className="detail">
            <div className="type">running on</div>
            <div className="value">
              {host}
              <Tooltip
                text={data.alertSeverity}
                placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
              >
                <span
                  className={`circle ${blockColor(
                    data.alertSeverity,
                    data.reporting
                  )}`}
                />
              </Tooltip>
            </div>
          </div>
        </div>
        <div className="meta">
          <div className="detail">
            <div className="type">cpu</div>
            <div className="value">{num.percentFormatted(data.cpuPercent)}</div>
          </div>
          <div className="detail">
            <div className="type">mem</div>
            <div className="value">
              {num.percentFormatted(data.memoryUsedPercent)}
            </div>
          </div>
          <div className="detail">
            <div className="type">vol</div>
            <div className="value">
              {num.percentFormatted(data.diskUsedPercent)}
            </div>
          </div>
          <div className="detail link">
            <Button
              type={Button.TYPE.PLAIN_NEUTRAL}
              iconType={
                Button.ICON_TYPE.INTERFACE__ARROW__ARROW_DIAGONAL_TOP_RIGHT
              }
              sizeType={Button.SIZE_TYPE.LARGE}
              onClick={() => openLink(data.guid, 'entity')}
            />
          </div>
        </div>
      </div>
    ) : null;
  }
}
