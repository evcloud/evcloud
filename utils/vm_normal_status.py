
def vm_normal_status(vm, flag=False):
    """
    检测 虚拟机的状态:搁置或正常。搁置状态不允许做其他操作（除恢复虚拟机）

    flag：用于虚拟机恢复时或其他需要的情况下
    """
    if flag or not vm:
        return True

    if vm.vm_status != vm.VmStatus.NORMAL.value:
        return False

    return True