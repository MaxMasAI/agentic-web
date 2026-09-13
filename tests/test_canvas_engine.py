import unittest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.canvas_engine import (
    CanvasEventBroker, CanvasNodeData, ConnectionEdgeData,
    ToolCallPayload, NodeContextStreamData, AutonomousAgentWorker
)

class TestCanvasEngine(unittest.TestCase):

    def setUp(self):
        self.broker = CanvasEventBroker.get_instance()
        self.broker.nodes.clear()
        self.broker.edges.clear()
        self.broker.edge_histories.clear()
        self.broker._subscribers.clear()

    def test_broker_registration_and_edges(self):
        node1 = CanvasNodeData(node_id="n1", node_type="terminal", title="Terminal 1", pos_x=0, pos_y=0)
        node2 = CanvasNodeData(node_id="n2", node_type="agent", title="Agent 1", pos_x=200, pos_y=0)
        
        self.broker.register_node(node1)
        self.broker.register_node(node2)
        
        self.assertIn("n1", self.broker.nodes)
        self.assertIn("n2", self.broker.nodes)

        edge = ConnectionEdgeData(
            edge_id="e1",
            source_node_id="n1",
            source_port="right",
            target_node_id="n2",
            target_port="top",
            data_type="shell_stream"
        )
        self.broker.add_edge(edge)
        
        self.assertEqual(self.broker.get_downstream_nodes("n1"), ["n2"])
        self.assertEqual(self.broker.get_upstream_nodes("n2"), ["n1"])

    def test_edge_history_and_stream_routing(self):
        node1 = CanvasNodeData(node_id="n1", node_type="terminal", title="Terminal 1", pos_x=0, pos_y=0)
        node2 = CanvasNodeData(node_id="n2", node_type="agent", title="Agent 1", pos_x=200, pos_y=0)
        self.broker.register_node(node1)
        self.broker.register_node(node2)

        edge = ConnectionEdgeData(
            edge_id="e1",
            source_node_id="n1",
            source_port="right",
            target_node_id="n2",
            target_port="left",
            data_type="shell_stream"
        )
        self.broker.add_edge(edge)

        received_streams = []
        def on_stream(s: NodeContextStreamData):
            received_streams.append(s)

        self.broker.subscribe("n2", on_stream)

        # Publish stream from node 1
        stream = NodeContextStreamData(
            stream_id="s1",
            source_node_id="n1",
            source_type="terminal",
            target_node_id=None,
            payload_type="stdout",
            content="Directory listing: app.py, requirements.txt"
        )
        self.broker.publish_stream(stream)

        self.assertEqual(len(received_streams), 1)
        self.assertEqual(received_streams[0].content, "Directory listing: app.py, requirements.txt")
        self.assertEqual(received_streams[0].target_node_id, "n2")

        # Verify edge history recorded
        hist = self.broker.get_edge_history("e1")
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["payload_type"], "stdout")

    def test_tool_call_execution(self):
        worker = AutonomousAgentWorker(node_id="agent_test", goal="Test tool execution")
        tool = ToolCallPayload(
            call_id="call_1",
            tool_name="run_command",
            arguments={"cmd": "python -c \"print('Hello Canvas')\""}
        )
        result = worker._execute_tool(tool)
        self.assertEqual(result.status, "success")
        self.assertIn("Hello Canvas", result.result)
        self.assertEqual(result.exit_code, 0)

    def test_recursive_node_spawning_tool(self):
        worker = AutonomousAgentWorker(node_id="agent_spawner", goal="Spawn parallel worker")
        spawn_events = []
        self.broker.node_spawn_requested.connect(lambda nt, t, x, y, a: spawn_events.append((nt, t)))

        tool = ToolCallPayload(
            call_id="call_spawn",
            tool_name="create_node",
            arguments={"node_type": "terminal", "title": "Parallel Test Node", "cmd": "dir"}
        )
        res = worker._execute_tool(tool)
        self.assertEqual(res.status, "success")
        self.assertEqual(len(spawn_events), 1)
        self.assertEqual(spawn_events[0][0], "terminal")
        self.assertEqual(spawn_events[0][1], "Parallel Test Node")

    def test_session_export_and_import(self):
        node1 = CanvasNodeData(node_id="n_a", node_type="terminal", title="A", pos_x=10, pos_y=20)
        node2 = CanvasNodeData(node_id="n_b", node_type="file_diff", title="B", pos_x=300, pos_y=50)
        self.broker.register_node(node1)
        self.broker.register_node(node2)

        edge = ConnectionEdgeData(
            edge_id="e_ab",
            source_node_id="n_a",
            source_port="right",
            target_node_id="n_b",
            target_port="left"
        )
        self.broker.add_edge(edge)

        export_data = self.broker.export_session_dict()
        self.assertEqual(len(export_data["nodes"]), 2)
        self.assertEqual(len(export_data["edges"]), 1)

        # Clear and re-import
        self.broker.import_session_dict(export_data)
        self.assertEqual(len(self.broker.nodes), 0)  # import_session_dict resets broker dicts for UI reconstruct

if __name__ == "__main__":
    unittest.main()
