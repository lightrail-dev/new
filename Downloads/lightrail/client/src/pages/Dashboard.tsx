import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { TrendingUp, Zap, Network, CheckCircle2, AlertCircle } from "lucide-react";

interface BaselineMetrics {
  total_training_time_s: number;
  avg_step_time_ms: number;
  avg_loss: number;
  mock_gpu_util_percent: number;
  num_steps: number;
  batch_size: number;
  world_size: number;
}

interface RoutingPlan {
  optimization_status: string;
  num_gpus: number;
  total_collectives_analyzed: number;
  estimated_improvement_percent: number;
  link_utilization_before_optimization: {
    max_utilization: number;
    avg_utilization: number;
  };
  link_utilization_after_optimization: {
    max_utilization: number;
    avg_utilization: number;
  };
}

interface EnforcementPlan {
  plan_version: string;
  estimated_training_time_reduction_percent: number;
  safety_validation: {
    topology_match: boolean;
    link_capacity_check: boolean;
    memory_safety_check: boolean;
    validation_result: string;
  };
}

export default function Dashboard() {
  const [baselineData, setBaselineData] = useState<BaselineMetrics | null>(null);
  const [routingData, setRoutingData] = useState<RoutingPlan | null>(null);
  const [enforcementData, setEnforcementData] = useState<EnforcementPlan | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load mock data from public folder
    const loadData = async () => {
      try {
        // In a real scenario, these would be loaded from the actual pipeline output files
        // For now, we'll use mock data embedded in the component
        const mockBaseline: BaselineMetrics = {
          total_training_time_s: 3.07,
          avg_step_time_ms: 30.69,
          avg_loss: 0.37,
          mock_gpu_util_percent: 76.85,
          num_steps: 100,
          batch_size: 32,
          world_size: 8,
        };

        const mockRouting: RoutingPlan = {
          optimization_status: "MOCK_OPTIMAL",
          num_gpus: 8,
          total_collectives_analyzed: 305,
          estimated_improvement_percent: 17.59,
          link_utilization_before_optimization: {
            max_utilization: 0.4887,
            avg_utilization: 0.3282,
          },
          link_utilization_after_optimization: {
            max_utilization: 0.391,
            avg_utilization: 0.2461,
          },
        };

        const mockEnforcement: EnforcementPlan = {
          plan_version: "1.0",
          estimated_training_time_reduction_percent: 17.59,
          safety_validation: {
            topology_match: true,
            link_capacity_check: true,
            memory_safety_check: true,
            validation_result: "PASS",
          },
        };

        setBaselineData(mockBaseline);
        setRoutingData(mockRouting);
        setEnforcementData(mockEnforcement);
        setLoading(false);
      } catch (error) {
        console.error("Error loading data:", error);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading LightRail Dashboard...</p>
        </div>
      </div>
    );
  }

  const utilizationData = [
    {
      name: "Before Optimization",
      max: (baselineData && routingData) ? Math.round(routingData.link_utilization_before_optimization.max_utilization * 100) : 0,
      avg: (baselineData && routingData) ? Math.round(routingData.link_utilization_before_optimization.avg_utilization * 100) : 0,
    },
    {
      name: "After Optimization",
      max: (baselineData && routingData) ? Math.round(routingData.link_utilization_after_optimization.max_utilization * 100) : 0,
      avg: (baselineData && routingData) ? Math.round(routingData.link_utilization_after_optimization.avg_utilization * 100) : 0,
    },
  ];

  const performanceData = [
    { name: "Baseline", value: 100 },
    { name: "Optimized", value: 100 - (routingData?.estimated_improvement_percent || 0) },
  ];

  const COLORS = ["#3b82f6", "#10b981"];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="container py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">LightRail Fabric OS</h1>
              <p className="text-muted-foreground mt-2">MVP Dashboard - Performance Optimization Pipeline</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-700">Pipeline Complete</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-8">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
            <TabsTrigger value="topology">Topology</TabsTrigger>
            <TabsTrigger value="enforcement">Enforcement</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Training Time */}
              <Card className="border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Training Time
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-foreground">{baselineData?.total_training_time_s.toFixed(2)}s</div>
                  <p className="text-xs text-muted-foreground mt-2">Baseline measurement</p>
                </CardContent>
              </Card>

              {/* Avg Step Time */}
              <Card className="border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Avg Step Time
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-foreground">{baselineData?.avg_step_time_ms.toFixed(2)}ms</div>
                  <p className="text-xs text-muted-foreground mt-2">Per training step</p>
                </CardContent>
              </Card>

              {/* GPU Utilization */}
              <Card className="border-border shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Network className="w-4 h-4" />
                    GPU Utilization
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-foreground">{baselineData?.mock_gpu_util_percent.toFixed(1)}%</div>
                  <p className="text-xs text-muted-foreground mt-2">Average across 8 GPUs</p>
                </CardContent>
              </Card>

              {/* Optimization Gain */}
              <Card className="border-border shadow-sm hover:shadow-md transition-shadow bg-emerald-50 border-emerald-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-emerald-700 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Estimated Improvement
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-emerald-700">{routingData?.estimated_improvement_percent.toFixed(2)}%</div>
                  <p className="text-xs text-emerald-600 mt-2">Training time reduction</p>
                </CardContent>
              </Card>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pipeline Status */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Pipeline Status</CardTitle>
                  <CardDescription>Execution summary of all 6 steps</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    {[
                      { step: "Step 1", name: "Baseline Measurement", status: "complete" },
                      { step: "Step 2", name: "Topology Discovery", status: "complete" },
                      { step: "Step 3", name: "NCCL Interception", status: "complete" },
                      { step: "Step 4", name: "Collective Metadata", status: "complete" },
                      { step: "Step 5", name: "Mathematical Optimization", status: "complete" },
                      { step: "Step 6", name: "Routing Enforcement", status: "complete" },
                    ].map((item) => (
                      <div key={item.step} className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm text-foreground">{item.step}</p>
                          <p className="text-xs text-muted-foreground">{item.name}</p>
                        </div>
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Cluster Configuration */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Cluster Configuration</CardTitle>
                  <CardDescription>Hardware and topology details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Number of GPUs</p>
                      <p className="text-lg font-bold text-foreground">{routingData?.num_gpus}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Collectives Analyzed</p>
                      <p className="text-lg font-bold text-foreground">{routingData?.total_collectives_analyzed}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Batch Size</p>
                      <p className="text-lg font-bold text-foreground">{baselineData?.batch_size}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Training Steps</p>
                      <p className="text-lg font-bold text-foreground">{baselineData?.num_steps}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Metrics Tab */}
          <TabsContent value="metrics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Link Utilization Comparison */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Link Utilization Comparison</CardTitle>
                  <CardDescription>Before and after optimization</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={utilizationData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: "#fff", border: "1px solid #e5e7eb" }}
                        formatter={(value) => `${value}%`}
                      />
                      <Legend />
                      <Bar dataKey="max" fill="#3b82f6" name="Max Utilization" />
                      <Bar dataKey="avg" fill="#10b981" name="Avg Utilization" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Performance Improvement */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Performance Improvement</CardTitle>
                  <CardDescription>Estimated training time reduction</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-center">
                  <div className="text-center">
                    <div className="relative w-32 h-32 mx-auto mb-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={performanceData}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={65}
                            paddingAngle={2}
                            dataKey="value"
                          >
                            {COLORS.map((color, index) => (
                              <Cell key={`cell-${index}`} fill={color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="text-3xl font-bold text-emerald-600">{routingData?.estimated_improvement_percent.toFixed(2)}%</p>
                    <p className="text-sm text-muted-foreground mt-2">Faster Training</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Topology Tab */}
          <TabsContent value="topology" className="space-y-6">
            <Card className="border-border shadow-sm">
              <CardHeader>
                <CardTitle>GPU Cluster Topology</CardTitle>
                <CardDescription>8-GPU NVLink connected cluster with optimized routing</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-slate-50 rounded-lg p-8 border border-slate-200">
                  <div className="flex items-center justify-center h-64">
                    <div className="grid grid-cols-4 gap-4">
                      {Array.from({ length: 8 }).map((_, i) => (
                        <div
                          key={i}
                          className="w-12 h-12 rounded-lg bg-blue-500 text-white flex items-center justify-center font-bold text-sm border-2 border-blue-600 shadow-md"
                        >
                          GPU{i}
                        </div>
                      ))}
                    </div>
                  </div>
                  <p className="text-center text-sm text-muted-foreground mt-4">
                    Fully connected NVLink topology with 600 Gbps per link
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Enforcement Tab */}
          <TabsContent value="enforcement" className="space-y-6">
            <Card className="border-border shadow-sm">
              <CardHeader>
                <CardTitle>Safety Validation</CardTitle>
                <CardDescription>Enforcement plan validation checks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {enforcementData && [
                  { check: "Topology Match", status: enforcementData.safety_validation.topology_match },
                  { check: "Link Capacity Check", status: enforcementData.safety_validation.link_capacity_check },
                  { check: "Memory Safety Check", status: enforcementData.safety_validation.memory_safety_check },
                ].map((item) => (
                  <div key={item.check} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <span className="font-medium text-sm text-foreground">{item.check}</span>
                    <div className="flex items-center gap-2">
                      {item.status ? (
                        <>
                          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                          <span className="text-sm text-emerald-600 font-medium">PASS</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-5 h-5 text-red-600" />
                          <span className="text-sm text-red-600 font-medium">FAIL</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardHeader>
                <CardTitle>Enforcement Configuration</CardTitle>
                <CardDescription>Routing enforcement plan details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Plan Version</p>
                    <p className="text-lg font-bold text-foreground">{enforcementData?.plan_version}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Estimated Improvement</p>
                    <p className="text-lg font-bold text-emerald-600">{enforcementData?.estimated_training_time_reduction_percent.toFixed(2)}%</p>
                  </div>
                </div>
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <strong>Routing Strategy:</strong> LightRail_Optimized with FIFO collective staging and 128 MB buffer
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
