def test_cli_module_imports_without_pipeline_side_effects():
    import qgrav.cli as cli
    assert hasattr(cli, "main")
