// Test fixture only (exercises the runtime contract); not used by agents.
import * as d3 from "d3";

export default function render(el, { data, params, width, height, theme }) {
  const rows = data.counts;
  const m = { l: 230, r: 20, t: 16, b: 28 };
  const svg = d3.select(el).append("svg").attr("width", width).attr("height", height);
  const g = svg.append("g");
  function draw(p) {
    g.selectAll("*").remove();
    const top = rows.slice().sort((a, b) => b.n - a.n).slice(0, p.topN);
    const x = d3.scaleLinear().domain([0, d3.max(top, (d) => d.n)]).range([m.l, width - m.r]);
    const y = d3.scaleBand().domain(top.map((d) => d.primary_field)).range([m.t, height - m.b]).padding(0.15);
    g.selectAll("rect").data(top).join("rect")
      .attr("x", m.l).attr("y", (d) => y(d.primary_field)).attr("width", (d) => x(d.n) - m.l)
      .attr("height", y.bandwidth()).attr("fill", theme.categorical[0])
      .attr("data-id", (d) => d.primary_field).attr("data-type", "field").attr("data-label", (d) => d.primary_field);
    g.append("g").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y));
    g.append("g").attr("transform", `translate(0,${height - m.b})`).call(d3.axisBottom(x));
  }
  draw(params);
  return { update(p) { draw(p); } };
}
