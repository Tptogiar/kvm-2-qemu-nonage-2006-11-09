# kvm-qemu-nonage-2
KVM & QEMU 早期源码阅读，添加了注释 (此时的KVM还没被纳入到Linux内核中，KVM相关的功能也还没完全嵌入到QEMU中) 

## 目录结构
```
├── configure
├── kernel                 // KVM源码
├── kvm
├── kvm.spec
├── kvm_stat
├── Makefile
├── management_service
├── qemu                   // 配套的QEMU源码
├── README.md
├── scripts
├── test_env
├── tptogiar
└── user                  // 本应该嵌入QEMU中的KVM相关的功能，但是还没嵌入


```
