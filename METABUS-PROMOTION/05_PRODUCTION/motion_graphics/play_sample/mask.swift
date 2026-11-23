// macOS Vision 전경(인물) 누끼 → 투명 PNG
// 사용: swift mask.swift <입력.png> <출력.png>
import Foundation
import Vision
import CoreImage

let args = CommandLine.arguments
guard args.count == 3 else {
    FileHandle.standardError.write("usage: swift mask.swift in.png out.png\n".data(using: .utf8)!)
    exit(2)
}
let input = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])

let handler = VNImageRequestHandler(url: input)
let request = VNGenerateForegroundInstanceMaskRequest()
do {
    try handler.perform([request])
    guard let obs = request.results?.first else {
        FileHandle.standardError.write("no foreground found\n".data(using: .utf8)!)
        exit(1)
    }
    let buffer = try obs.generateMaskedImage(ofInstances: obs.allInstances, from: handler, croppedToInstancesExtent: false)
    let image = CIImage(cvPixelBuffer: buffer)
    let ctx = CIContext()
    try ctx.writePNGRepresentation(of: image, to: output, format: .RGBA8,
                                   colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
    print("ok instances=\(obs.allInstances.count) -> \(output.path)")
} catch {
    FileHandle.standardError.write("error: \(error)\n".data(using: .utf8)!)
    exit(1)
}
