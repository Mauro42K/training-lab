# PBXProj Wiring Note (Phase 3 / Block 6.2)

## Problema
Los archivos de `DesignSystemDemo/DesignSystemDemo/TrainingLab/` existían en filesystem pero no estaban cableados correctamente en `project.pbxproj`, por lo que el target `DesignSystemDemo` no compilaba parte de los contratos online-first.

## Solución aplicada
Se realizó wiring manual en `DesignSystemDemo/DesignSystemDemo.xcodeproj/project.pbxproj` para:
- agregar `PBXFileReference` de fuentes TrainingLab faltantes,
- mantener grupos visibles por dominio (`App`, `Clients`, `Models`, `Services`, `Repositories`),
- agregar `PBXBuildFile` y entradas en `PBXSourcesBuildPhase` para contratos y repositorios de Phase 3.

## Resultado
Con el wiring aplicado, los builds obligatorios de Phase 3 quedaron en PASS:
- iOS Simulator (`iPhone 17 Pro`)
- macOS
