import React from 'react';
import PropTypes from 'prop-types';

import num from '../../utils/number';

export default class DomainStats extends React.Component {
  static propTypes = {
    data: PropTypes.object,
    type: PropTypes.string
  };

  render() {
    const { data, type } = this.props;

    return data && type ? (
      <div className="infra">
        <div className="title">
          <div className="detail">
            <div className="value all-caps">{type}</div>
          </div>
        </div>
        <div className="meta">
          {Object.keys(data).map(key => (
            <div className="detail" key={key}>
              <div className="type">{key}</div>
              <div className="value">{num.defaultFormatted(data[key])}</div>
            </div>
          ))}
        </div>
      </div>
    ) : null;
  }
}
