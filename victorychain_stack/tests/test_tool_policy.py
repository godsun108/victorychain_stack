import pytest
from src.victory_impact.tool_policy import ToolManifest,make_receipt
D="a"*64

def test_manifest_permits_declared_action():
 m=ToolManifest("chain-reader","1",("read.state",),True)
 assert m.permits("read.state") and not m.permits("write.state")

def test_read_only_manifest_cannot_advertise_privileged_action():
 with pytest.raises(ValueError,match="privileged"):
  ToolManifest("bad","1",("treasury.pay",),True).validate()

def test_undeclared_tool_action_fails():
 with pytest.raises(ValueError,match="not permitted"):
  make_receipt(ToolManifest("r","1",("read.state",)), "read.secret",D,{})

def test_receipt_binds_result():
 m=ToolManifest("r","1",("read.state",))
 assert make_receipt(m,"read.state",D,{"x":1}).digest()!=make_receipt(m,"read.state",D,{"x":2}).digest()
