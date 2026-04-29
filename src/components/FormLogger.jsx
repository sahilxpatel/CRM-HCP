import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { createInteraction } from "../redux/interactionsSlice";

const initialState = {
  hcp_name: "",
  date: "",
  interaction_type: "",
  notes: "",
};

const FormLogger = () => {
  const dispatch = useDispatch();
  const { loading, error } = useSelector((state) => state.interactions);
  const [formState, setFormState] = useState(initialState);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormState((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await dispatch(createInteraction(formState));
    setFormState(initialState);
  };

  return (
    <div className="card">
      <h2>Structured Form Logger</h2>
      <form className="field-group" onSubmit={handleSubmit}>
        <div className="field">
          <label>HCP Name</label>
          <input
            name="hcp_name"
            value={formState.hcp_name}
            onChange={handleChange}
            placeholder="Dr. Alex Smith"
            required
          />
        </div>
        <div className="field">
          <label>Date</label>
          <input
            type="date"
            name="date"
            value={formState.date}
            onChange={handleChange}
            required
          />
        </div>
        <div className="field">
          <label>Interaction Type</label>
          <input
            name="interaction_type"
            value={formState.interaction_type}
            onChange={handleChange}
            placeholder="Clinic visit"
            required
          />
        </div>
        <div className="field">
          <label>Notes</label>
          <textarea
            name="notes"
            rows="4"
            value={formState.notes}
            onChange={handleChange}
            placeholder="Key highlights from the visit"
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? "Logging..." : "Log Interaction"}
        </button>
        {error ? <span>{error}</span> : null}
      </form>
    </div>
  );
};

export default FormLogger;
