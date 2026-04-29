import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { loadInteractions } from "../redux/interactionsSlice";

const InteractionList = () => {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector((state) => state.interactions);

  useEffect(() => {
    dispatch(loadInteractions());
  }, [dispatch]);

  return (
    <div className="card">
      <h2>Interaction History</h2>
      {loading ? <p>Loading interactions...</p> : null}
      {error ? <p>{error}</p> : null}
      {items.length === 0 && !loading ? (
        <p>No interactions yet. Log via form or chat.</p>
      ) : null}
      {items.map((item) => (
        <div key={item.id} className="list-item">
          <div className="badge">{item.interaction_type}</div>
          <h3>{item.hcp_name}</h3>
          <div className="summary-label">
            {item.summary ? "AI Summary" : "Notes"}
          </div>
          <p className="summary-text">{item.summary || item.notes}</p>
          <small>{item.date}</small>
        </div>
      ))}
    </div>
  );
};

export default InteractionList;
