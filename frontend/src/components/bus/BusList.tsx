import type { Bus } from '../../types/domain';

type BusListProps = {
  buses: Bus[];
  isLoading: boolean;
};

export function BusList({ buses, isLoading }: BusListProps) {
  return (
    <section className="panel" aria-label="Bus list">
      <div className="panel-header">
        <div>
          <h2>Buses</h2>
          <p>Registered fleet</p>
        </div>
      </div>

      {isLoading ? (
        <p className="empty-state">Loading buses</p>
      ) : buses.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Bus ID</th>
                <th scope="col">Registration Number</th>
                <th scope="col">Route ID</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {buses.map((bus) => (
                <tr key={bus.id}>
                  <td>{bus.id}</td>
                  <td>{bus.registration_number}</td>
                  <td>{bus.route_id ?? '-'}</td>
                  <td>
                    <span className="status-pill">{bus.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="empty-state">No buses available.</p>
      )}
    </section>
  );
}
