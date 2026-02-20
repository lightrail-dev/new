import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter } from "recharts";
import { Upload, Zap, TrendingUp, Network, CheckCircle2, AlertCircle, Download, Plus, Trash2 } from "lucide-react";

interface BenchmarkRun {
  id: string;
  name: string;
  timestamp: string;
  baseline_metrics: {
    total_training_time_s: number;
    avg_step_time_ms: number;
    avg_loss: number;
    mock_gpu_util_percent: number;
    num_steps: number;
    batch_size: number;
    world_size: number;
  };
  routing_plan: {
    estimated_improvement_percent: number;
    link_utilization_before_optimization: {
      max_utilization: number;
      avg_utilization: number;
    };
    link_utilization_after_optimization: {
      max_utilization: number;
      avg_utilization: number;
    };
  };
}

export default function BenchmarkTool() {
  const [benchmarks, setBenchmarks] = useState<BenchmarkRun[]>([
    {
      id: "bench-001",
      name: "Production Run - Dec 14",
      timestamp: "2025-12-14T23:20:00Z",
      baseline_metrics: {
        total_training_time_s: 3.07,
        avg_step_time_ms: 30.69,
        avg_loss: 0.37,
        mock_gpu_util_percent: 76.85,
        num_steps: 100,
        batch_size: 32,
        world_size: 8,
      },
      routing_plan: {
        estimated_improvement_percent: 17.59,
        link_utilization_before_optimization: {
          max_utilization: 0.4887,
          avg_utilization: 0.3282,
        },
        link_utilization_after_optimization: {
          max_utilization: 0.391,
          avg_utilization: 0.2461,
        },
      },
    },
  ]);

  const [selectedBenchmark, setSelectedBenchmark] = useState<BenchmarkRun | null>(benchmarks[0]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target?.result as string);
          const newBenchmark: BenchmarkRun = {
            id: `bench-${Date.now()}`,
            name: file.name.replace(".json", ""),
            timestamp: new Date().toISOString(),
            baseline_metrics: data.baseline_metrics || data,
            routing_plan: data.routing_plan || data,
          };
          setBenchmarks([...benchmarks, newBenchmark]);
          setSelectedBenchmark(newBenchmark);
        } catch (error) {
          console.error("Error parsing JSON:", error);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleDeleteBenchmark = (id: string) => {
    const filtered = benchmarks.filter((b) => b.id !== id);
    setBenchmarks(filtered);
    if (selectedBenchmark?.id === id) {
      setSelectedBenchmark(filtered[0] || null);
    }
  };

  if (!selectedBenchmark) {
    return (
      <div className="min-h-screen bg-background">
        <div className="border-b border-[#333333] bg-card">
          <div className="container py-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-[#00ff00]">LightRail Fabric OS</h1>
                <p className="text-subtle mt-2">Benchmarking & Performance Analysis Tool</p>
              </div>
            </div>
          </div>
        </div>

        <div className="container py-12">
          <div className="text-center">
            <p className="text-subtle mb-8 text-lg">No benchmarks loaded. Upload a benchmark file to get started.</p>
            <label>
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button className="bg-[#00ff00] text-black hover:bg-[#00dd00] font-semibold">
                <Upload className="w-4 h-4 mr-2" />
                Upload Benchmark
              </Button>
            </label>
          </div>
        </div>
      </div>
    );
  }

  const comparisonData = benchmarks.map((b) => ({
    name: b.name.substring(0, 15),
    improvement: b.routing_plan.estimated_improvement_percent,
    avgUtil: Math.round(b.routing_plan.link_utilization_after_optimization.avg_utilization * 100),
  }));

  const utilizationData = [
    {
      name: "Before",
      value: Math.round(selectedBenchmark.routing_plan.link_utilization_before_optimization.avg_utilization * 100),
    },
    {
      name: "After",
      value: Math.round(selectedBenchmark.routing_plan.link_utilization_after_optimization.avg_utilization * 100),
    },
  ];

  const COLORS = ["#00ff00", "#ffd700"];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-[#333333] bg-card">
        <div className="container py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-[#00ff00]">LightRail Fabric OS</h1>
              <p className="text-subtle mt-2">Benchmarking & Performance Analysis Tool</p>
            </div>
            <label>
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button className="bg-[#00ff00] text-black hover:bg-[#00dd00] font-semibold">
                <Plus className="w-4 h-4 mr-2" />
                Add Benchmark
              </Button>
            </label>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          {/* Benchmark Selector */}
          <div className="lg:col-span-1">
            <Card className="border-[#333333] bg-card">
              <CardHeader>
                <CardTitle className="text-clear text-lg">Benchmarks</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {benchmarks.map((b) => (
                  <div
                    key={b.id}
                    className={`p-3 rounded-lg cursor-pointer transition-all ${
                      selectedBenchmark.id === b.id
                        ? "bg-[#00ff00] bg-opacity-20 border border-[#00ff00]"
                        : "bg-[#2a2a2a] hover:bg-[#333333] border border-[#333333]"
                    }`}
                    onClick={() => setSelectedBenchmark(b)}
                  >
                    <p className="text-clear text-sm font-semibold truncate">{b.name}</p>
                    <p className="text-subtle text-xs">{new Date(b.timestamp).toLocaleDateString()}</p>
                    {selectedBenchmark.id === b.id && benchmarks.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteBenchmark(b.id);
                        }}
                        className="mt-2 text-xs text-red-400 hover:text-red-300 flex items-center gap-1 font-semibold"
                      >
                        <Trash2 className="w-3 h-3" />
                        Delete
                      </button>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Key Metrics */}
          <div className="lg:col-span-3 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="border-[#333333] bg-card">
                <CardHeader className="pb-3">
                  <CardTitle className="text-label flex items-center gap-2">
                    <Zap className="w-4 h-4 text-[#00ff00]" />
                    Training Time
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-metric">{selectedBenchmark.baseline_metrics.total_training_time_s.toFixed(2)}s</div>
                  <p className="text-subtle text-xs mt-2">Baseline measurement</p>
                </CardContent>
              </Card>

              <Card className="border-[#333333] bg-card">
                <CardHeader className="pb-3">
                  <CardTitle className="text-label flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#ffd700]" />
                    Optimization Gain
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-metric-secondary">{selectedBenchmark.routing_plan.estimated_improvement_percent.toFixed(2)}%</div>
                  <p className="text-subtle text-xs mt-2">Estimated improvement</p>
                </CardContent>
              </Card>

              <Card className="border-[#333333] bg-card">
                <CardHeader className="pb-3">
                  <CardTitle className="text-label flex items-center gap-2">
                    <Network className="w-4 h-4 text-[#00ff00]" />
                    GPU Utilization
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-metric">{selectedBenchmark.baseline_metrics.mock_gpu_util_percent.toFixed(1)}%</div>
                  <p className="text-subtle text-xs mt-2">Average across {selectedBenchmark.baseline_metrics.world_size} GPUs</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Analysis Tabs */}
        <Tabs defaultValue="performance" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-card border border-[#333333]">
            <TabsTrigger value="performance" className="text-clear">Performance</TabsTrigger>
            <TabsTrigger value="utilization" className="text-clear">Utilization</TabsTrigger>
            <TabsTrigger value="comparison" className="text-clear">Comparison</TabsTrigger>
          </TabsList>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="border-[#333333] bg-card">
                <CardHeader>
                  <CardTitle className="text-clear">Step Time Analysis</CardTitle>
                  <CardDescription className="text-subtle">Average time per training step</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <p className="text-label mb-2">Baseline Step Time</p>
                      <div className="text-metric">{selectedBenchmark.baseline_metrics.avg_step_time_ms.toFixed(2)}ms</div>
                    </div>
                    <div>
                      <p className="text-label mb-2">Estimated Optimized</p>
                      <div className="text-metric-secondary">
                        {(selectedBenchmark.baseline_metrics.avg_step_time_ms * (1 - selectedBenchmark.routing_plan.estimated_improvement_percent / 100)).toFixed(2)}ms
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-[#333333] bg-card">
                <CardHeader>
                  <CardTitle className="text-clear">Cluster Configuration</CardTitle>
                  <CardDescription className="text-subtle">Hardware specifications</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-label">GPUs</p>
                      <p className="text-metric text-2xl mt-1">{selectedBenchmark.baseline_metrics.world_size}</p>
                    </div>
                    <div>
                      <p className="text-label">Batch Size</p>
                      <p className="text-metric text-2xl mt-1">{selectedBenchmark.baseline_metrics.batch_size}</p>
                    </div>
                    <div>
                      <p className="text-label">Training Steps</p>
                      <p className="text-metric text-2xl mt-1">{selectedBenchmark.baseline_metrics.num_steps}</p>
                    </div>
                    <div>
                      <p className="text-label">Loss</p>
                      <p className="text-metric text-2xl mt-1">{selectedBenchmark.baseline_metrics.avg_loss.toFixed(4)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Utilization Tab */}
          <TabsContent value="utilization" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="border-[#333333] bg-card">
                <CardHeader>
                  <CardTitle className="text-clear">Link Utilization</CardTitle>
                  <CardDescription className="text-subtle">Before and after optimization</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      data={[
                        {
                          name: "Before",
                          max: Math.round(selectedBenchmark.routing_plan.link_utilization_before_optimization.max_utilization * 100),
                          avg: Math.round(selectedBenchmark.routing_plan.link_utilization_before_optimization.avg_utilization * 100),
                        },
                        {
                          name: "After",
                          max: Math.round(selectedBenchmark.routing_plan.link_utilization_after_optimization.max_utilization * 100),
                          avg: Math.round(selectedBenchmark.routing_plan.link_utilization_after_optimization.avg_utilization * 100),
                        },
                      ]}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
                      <XAxis dataKey="name" stroke="#a8a8a8" />
                      <YAxis stroke="#a8a8a8" />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #00ff00", color: "#f0f0f0" }}
                        formatter={(value) => `${value}%`}
                        labelStyle={{ color: "#f0f0f0" }}
                      />
                      <Legend wrapperStyle={{ color: "#f0f0f0" }} />
                      <Bar dataKey="max" fill="#00ff00" name="Max Utilization" />
                      <Bar dataKey="avg" fill="#ffd700" name="Avg Utilization" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-[#333333] bg-card">
                <CardHeader>
                  <CardTitle className="text-clear">Improvement Distribution</CardTitle>
                  <CardDescription className="text-subtle">Optimization impact</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-center">
                  <div className="text-center">
                    <ResponsiveContainer width={250} height={250}>
                      <PieChart>
                        <Pie
                          data={utilizationData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {COLORS.map((color, index) => (
                            <Cell key={`cell-${index}`} fill={color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => `${value}%`} contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #00ff00", color: "#f0f0f0" }} />
                      </PieChart>
                    </ResponsiveContainer>
                    <p className="text-subtle text-sm mt-4">
                      Utilization reduced by {(selectedBenchmark.routing_plan.link_utilization_before_optimization.avg_utilization - selectedBenchmark.routing_plan.link_utilization_after_optimization.avg_utilization).toFixed(4)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Comparison Tab */}
          <TabsContent value="comparison" className="space-y-6 mt-6">
            {benchmarks.length > 1 ? (
              <Card className="border-[#333333] bg-card">
                <CardHeader>
                  <CardTitle className="text-clear">Benchmark Comparison</CardTitle>
                  <CardDescription className="text-subtle">Performance across all uploaded benchmarks</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comparisonData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
                      <XAxis dataKey="name" stroke="#a8a8a8" />
                      <YAxis stroke="#a8a8a8" />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#1a1a1a", border: "1px solid #00ff00", color: "#f0f0f0" }}
                        formatter={(value) => `${value}%`}
                        labelStyle={{ color: "#f0f0f0" }}
                      />
                      <Legend wrapperStyle={{ color: "#f0f0f0" }} />
                      <Bar dataKey="improvement" fill="#00ff00" name="Improvement %" />
                      <Bar dataKey="avgUtil" fill="#ffd700" name="Avg Util %" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-[#333333] bg-card">
                <CardContent className="pt-6">
                  <p className="text-center text-subtle">Upload multiple benchmarks to compare performance metrics.</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
