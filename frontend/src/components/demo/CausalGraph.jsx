import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function CausalGraph({ incident }) {
  const svgRef = useRef(null);
  const graph = incident?.causal_graph;

  useEffect(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) return;

    const svgEl = svgRef.current;
    const width = svgEl.clientWidth || 760;
    const height = 420;

    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const defs = svg.append("defs");
    defs
      .append("marker")
      .attr("id", "arrow-pm")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 40)
      .attr("refY", 0)
      .attr("markerWidth", 7)
      .attr("markerHeight", 7)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#5b60a8");

    const nodes = graph.nodes.map((n) => ({ ...n }));
    const links = graph.edges.map((e) => ({ ...e }));

    const sim = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-560))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(46));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#2a3146")
      .attr("stroke-width", (d) => 1 + (d.confidence || 0.5) * 2.4)
      .attr("marker-end", "url(#arrow-pm)");

    const edgeLabel = svg
      .append("g")
      .selectAll("text")
      .data(links)
      .join("text")
      .attr("font-size", "9px")
      .attr("font-family", "JetBrains Mono")
      .attr("fill", "#6b7390")
      .attr("text-anchor", "middle")
      .text((d) => d.relationship);

    const node = svg
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(
        d3
          .drag()
          .on("start", (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node
      .append("circle")
      .attr("r", 34)
      .attr("fill", (d) => (d.is_root_cause ? "#2a0f1a" : "#11141f"))
      .attr("stroke", (d) => (d.is_root_cause ? "#ff4d6d" : "#2a3146"))
      .attr("stroke-width", (d) => (d.is_root_cause ? 2.5 : 1.5));

    node
      .filter((d) => d.is_root_cause)
      .append("circle")
      .attr("r", 34)
      .attr("fill", "none")
      .attr("stroke", "#ff4d6d")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.5)
      .append("animate")
      .attr("attributeName", "r")
      .attr("values", "34;46;34")
      .attr("dur", "2.4s")
      .attr("repeatCount", "indefinite");

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "-0.15em")
      .attr("font-size", "10px")
      .attr("font-family", "JetBrains Mono")
      .attr("font-weight", "700")
      .attr("fill", (d) => (d.is_root_cause ? "#ff708b" : "#7c5cff"))
      .text((d) => d.service);

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "1.15em")
      .attr("font-size", "8px")
      .attr("fill", "#7a7f9b")
      .text((d) => (d.event || "").split(" ").slice(0, 4).join(" "));

    sim.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      edgeLabel
        .attr("x", (d) => (d.source.x + d.target.x) / 2)
        .attr("y", (d) => (d.source.y + d.target.y) / 2 - 5);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => sim.stop();
  }, [graph]);

  const rootNode = graph?.nodes?.find((n) => n.is_root_cause);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="grid h-[420px] place-items-center text-center text-sm text-zinc-500">
        The causal graph appears once BlameMapper finishes its analysis.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {rootNode && (
        <div className="border-glow rounded-xl border border-rose/30 bg-rose/10 p-4">
          <div className="text-[10px] font-bold uppercase tracking-widest text-rose">
            🎯 Root cause · {rootNode.service}
          </div>
          <p className="mt-1 text-sm text-zinc-200">{rootNode.event}</p>
        </div>
      )}
      <div className="overflow-hidden rounded-xl border border-white/10 bg-ink-950/60">
        <svg ref={svgRef} className="w-full" style={{ height: 420 }} />
      </div>
    </div>
  );
}
