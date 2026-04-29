import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { fetchInteractions, logInteraction } from "../services/api";

export const loadInteractions = createAsyncThunk(
  "interactions/load",
  async () => fetchInteractions()
);

export const createInteraction = createAsyncThunk(
  "interactions/create",
  async (payload) => logInteraction(payload)
);

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: {
    items: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(loadInteractions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadInteractions.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(loadInteractions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "Failed to load interactions";
      })
      .addCase(createInteraction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.loading = false;
        state.items = [action.payload, ...state.items];
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "Failed to log interaction";
      });
  },
});

export default interactionsSlice.reducer;
