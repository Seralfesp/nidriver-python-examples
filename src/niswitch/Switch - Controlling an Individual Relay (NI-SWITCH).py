import niswitch

with niswitch.Session(resource_name="PXI2564", topology="2564/16-SPST", simulate=False, reset_device=False) as session:
    session.relay_control("k0", niswitch.RelayAction.CLOSE)
    session.wait_for_debounce()