import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

const METRICS = [
  "pack_voltage",
  "pack_current",
  "pack_temp",
  "state_of_charge",
  "min_cell_voltage",
  "bms_lv_input",
  "torque_feedback",
  "rpm",
  "flux_feedback",
];

const MAX_POINTS = 130;
const WINDOW_MS = 2 * 60 * 1000;
const CHART_HEIGHT = 200;

/** One column on narrow viewports (full-width charts); two columns from 768px up. */
function useTwoColumnChartGrid() {
  const [twoColumns, setTwoColumns] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(min-width: 768px)").matches : false
  );

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const onChange = () => setTwoColumns(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  return twoColumns;
}

const METRIC_CONFIG = {
  pack_voltage: { label: "Pack Voltage", unit: "V", color: "#f59e0b" },
  pack_current: { label: "Pack Current", unit: "A", color: "#38bdf8" },
  pack_temp: { label: "Pack Temp", unit: "°C", color: "#ef4444" },
  state_of_charge: { label: "State of Charge", unit: "%", color: "#10b981" },
  min_cell_voltage: { label: "Min Cell Voltage", unit: "V", color: "#fbbf24" },
  bms_lv_input: { label: "BMS LV Input", unit: "V", color: "#22d3ee" },
  torque_feedback: { label: "Torque Feedback", unit: "Nm", color: "#a78bfa" },
  rpm: { label: "RPM", unit: "rpm", color: "#f472b6" },
  flux_feedback: { label: "Flux Feedback", unit: "Wb", color: "#94a3b8" },
};

function formatAxisTime(timestampMs) {
  return new Date(timestampMs).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function seriesStats(points) {
  const nums = points
    .map((p) => Number(p.value))
    .filter(Number.isFinite);
  if (!nums.length) return { min: null, max: null, avg: null };
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const avg = nums.reduce((a, b) => a + b, 0) / nums.length;
  return { min, max, avg };
}

function MetricChart({ metric, data, windowEndMs }) {
  const cfg = METRIC_CONFIG[metric];
  const [thresholdInput, setThresholdInput] = useState("");

  const windowStartMs = windowEndMs - WINDOW_MS;
  const visibleData = useMemo(
    () => data.filter((point) => point.timestampMs >= windowStartMs),
    [data, windowStartMs]
  );

  const latest = visibleData.length ? visibleData[visibleData.length - 1]?.value : null;
  const { min, max, avg } = useMemo(() => seriesStats(visibleData), [visibleData]);

  const thresholdParsed = thresholdInput.trim() === "" ? NaN : Number(thresholdInput);
  const thresholdY = Number.isFinite(thresholdParsed) ? thresholdParsed : null;

  const fmt = (v) => (v !== null && Number.isFinite(v) ? `${Number(v).toFixed(2)} ${cfg.unit}` : "—");

  return (
    <div
      style={{
        backgroundColor: "#0f172a",
        border: "1px solid #1e293b",
        borderLeft: `3px solid ${cfg.color}`,
        borderRadius: "10px",
        padding: "16px",
        minWidth: 0,
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "8px",
          marginBottom: "10px",
        }}
      >
        <span style={{ color: "#94a3b8", fontSize: "12px", letterSpacing: "0.08em" }}>
          {cfg.label.toUpperCase()}
        </span>
        <span
          style={{
            color: cfg.color,
            fontWeight: "700",
            fontSize: "18px",
            fontFamily: "monospace",
          }}
        >
          {latest !== null && latest !== undefined ? `${Number(latest).toFixed(2)} ${cfg.unit}` : "—"}
        </span>
      </div>
      <div
        style={{
          fontSize: "11px",
          color: "#64748b",
          fontFamily: "monospace",
          marginBottom: "10px",
          lineHeight: 1.5,
        }}
      >
        <span>min {fmt(min)}</span>
        <span style={{ margin: "0 10px", color: "#334155" }}>|</span>
        <span>max {fmt(max)}</span>
        <span style={{ margin: "0 10px", color: "#334155" }}>|</span>
        <span>avg {fmt(avg)}</span>
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "10px",
          flexWrap: "wrap",
        }}
      >
        <label style={{ fontSize: "11px", color: "#94a3b8" }} htmlFor={`threshold-${metric}`}>
          Threshold
        </label>
        <input
          id={`threshold-${metric}`}
          type="text"
          inputMode="decimal"
          placeholder="e.g. 40"
          value={thresholdInput}
          onChange={(e) => setThresholdInput(e.target.value)}
          style={{
            width: "100px",
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "6px",
            color: "#e2e8f0",
            fontSize: "12px",
            fontFamily: "monospace",
            padding: "4px 8px",
          }}
        />
        <button
          type="button"
          onClick={() => setThresholdInput("")}
          style={{
            backgroundColor: "#334155",
            border: "none",
            borderRadius: "6px",
            color: "#e2e8f0",
            fontSize: "11px",
            padding: "4px 10px",
            cursor: "pointer",
          }}
        >
          Clear
        </button>
      </div>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <LineChart data={visibleData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            type="number"
            dataKey="timestampMs"
            domain={[windowStartMs, windowEndMs]}
            stroke="#334155"
            tick={false}
            ticks={false}
          />
          <YAxis stroke="#334155" tick={{ fontSize: 9, fill: "#475569" }} width={35} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "none",
              color: "#e2e8f0",
              fontSize: "12px",
            }}
            labelFormatter={(label) => formatAxisTime(label)}
            formatter={(v) => [`${Number(v).toFixed(2)} ${cfg.unit}`, cfg.label]}
          />
          {thresholdY !== null ? (
            <ReferenceLine
              y={thresholdY}
              stroke="#e879f9"
              strokeDasharray="4 4"
              label={{ value: "Threshold", fill: "#e879f9", fontSize: 10 }}
            />
          ) : null}
          <Line
            type="monotone"
            dataKey="value"
            stroke={cfg.color}
            dot={false}
            isAnimationActive={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function App() {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
  const twoColumnGrid = useTwoColumnChartGrid();

  const emptyBuffers = Object.fromEntries(METRICS.map((m) => [m, []]));

  const [buffers, setBuffers] = useState(emptyBuffers);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activeDuck, setActiveDuck] = useState("");
  const [ducks, setDucks] = useState([]);
  const [connected, setConnected] = useState(false);
  const [windowEndMs, setWindowEndMs] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setWindowEndMs(Date.now());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadDucks() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/ducks`);
        const json = await res.json();
        const list = Array.isArray(json?.ducks) ? json.ducks : [];
        if (cancelled) return;
        setDucks(list);
        if (!cancelled && list.length && !activeDuck) setActiveDuck(list[0]);
      } catch (e) {
        console.error("Failed to load ducks:", e);
      }
    }

    loadDucks();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let socket = null;

    async function hydrateAndConnect() {
      setBuffers(emptyBuffers);
      setLastUpdated(null);
      setConnected(false);

      if (!activeDuck) return;

      const nextBuffers = Object.fromEntries(METRICS.map((m) => [m, []]));
      try {
        for (const m of METRICS) {
          const res = await fetch(
            `${API_BASE_URL}/api/${encodeURIComponent(activeDuck)}/metrics/${m}`
          );
          const json = await res.json();
          const key = Object.keys(json || {})[0];
          const rawValues = Array.isArray(json?.[key]) ? json[key] : [];

          const points = rawValues
            .map((s) => {
              try {
                const obj = typeof s === "string" ? JSON.parse(s) : s;
                if (!obj?.timestamp || obj?.value === undefined) return null;
                return { timestamp: obj.timestamp, value: obj.value };
              } catch {
                return null;
              }
            })
            .filter(Boolean)
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

          nextBuffers[m] = points
            .map((p) => ({ timestampMs: new Date(p.timestamp).getTime(), value: p.value }))
            .filter((p) => Number.isFinite(p.timestampMs))
            .filter((p) => p.timestampMs >= Date.now() - WINDOW_MS)
            .slice(-MAX_POINTS);
        }
      } catch (e) {
        console.error("Hydration from Redis failed:", e);
      }

      if (cancelled) return;
      setBuffers(nextBuffers);
      setLastUpdated(new Date().toLocaleTimeString());

      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        if (cancelled) return;
        setConnected(true);
      };

      socket.onmessage = (event) => {
        if (cancelled) return;
        const message = JSON.parse(event.data);

        if (message.type === "data" && Array.isArray(message.records)) {
          const selectedDuck = activeDuck;
          setBuffers((prev) => {
            const next = { ...prev };
            let touched = false;

            for (const record of message.records) {
              if (record?.device_id !== selectedDuck) continue;

              const timestampMs = new Date(record.timestamp).getTime();
              if (!Number.isFinite(timestampMs)) continue;
              for (const m of METRICS) {
                if (record[m] !== undefined) {
                  touched = true;
                  const nextSeries = [...(next[m] || []), { timestampMs, value: record[m] }];
                  const minAllowedTimestamp = Date.now() - WINDOW_MS;
                  next[m] = nextSeries
                    .filter((point) => point.timestampMs >= minAllowedTimestamp)
                    .slice(-MAX_POINTS);
                }
              }
            }

            if (!touched) return prev;
            return next;
          });

          setLastUpdated(new Date().toLocaleTimeString());
        }
      };

      socket.onerror = (err) => {
        console.error("WebSocket Error:", err);
        if (!cancelled) setConnected(false);
      };

      socket.onclose = () => {
        if (!cancelled) setConnected(false);
      };
    }

    hydrateAndConnect();

    return () => {
      cancelled = true;
      setConnected(false);
      if (socket) socket.close();
    };
  }, [activeDuck]);

  return (
    <div
      style={{
        backgroundColor: "#020817",
        minHeight: "100vh",
        width: "100%",
        maxWidth: "100vw",
        padding: twoColumnGrid ? "24px clamp(16px, 4vw, 40px)" : "16px 12px",
        color: "#e2e8f0",
        fontFamily: "'Courier New', monospace",
        boxSizing: "border-box",
        overflowX: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          marginBottom: "24px",
          borderBottom: "1px solid #1e293b",
          paddingBottom: "16px",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "11px",
              color: "#475569",
              letterSpacing: "0.2em",
              marginBottom: "4px",
            }}
          >
            UCONN FORMULA SAE
          </div>
          <h1 style={{ margin: 0, fontSize: "22px", fontWeight: "800", letterSpacing: "0.05em" }}>
            TELEMETRY DASHBOARD
          </h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <select
            value={activeDuck}
            onChange={(e) => setActiveDuck(e.target.value)}
            style={{
              backgroundColor: "#1e293b",
              color: "#e2e8f0",
              border: "1px solid #334155",
              padding: "6px 10px",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          >
            {!ducks.length ? (
              <option value="" disabled>
                Loading...
              </option>
            ) : null}
            {ducks.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "6px",
              backgroundColor: connected ? "#052e16" : "#2d0a0a",
              border: `1px solid ${connected ? "#166534" : "#7f1d1d"}`,
              fontSize: "12px",
              color: connected ? "#4ade80" : "#f87171",
            }}
          >
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                backgroundColor: connected ? "#4ade80" : "#f87171",
                boxShadow: connected ? "0 0 6px #4ade80" : "none",
              }}
            />
            {connected ? "LIVE" : "OFFLINE"}
          </div>
        </div>
      </div>

      {lastUpdated && (
        <div style={{ fontSize: "11px", color: "#475569", marginBottom: "16px" }}>
          Last update: {lastUpdated}
        </div>
      )}

      <div
        style={{
          display: "grid",
          width: "100%",
          gridTemplateColumns: twoColumnGrid
            ? "repeat(2, minmax(0, 1fr))"
            : "minmax(0, 1fr)",
          gap: twoColumnGrid ? "20px" : "18px",
        }}
      >
        {METRICS.map((m) => (
          <MetricChart key={m} metric={m} data={buffers[m]} windowEndMs={windowEndMs} />
        ))}
      </div>
    </div>
  );
}
