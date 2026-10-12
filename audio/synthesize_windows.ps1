$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synthesizer = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    $voices = @($synthesizer.GetInstalledVoices() | Where-Object {
        $_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'zh-CN'
    })
    if ($voices.Count -eq 0) { throw 'No enabled zh-CN speech voice installed' }
    $synthesizer.SelectVoice($voices[0].VoiceInfo.Name)
    $format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(
        16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono)
    $synthesizer.SetOutputToWaveFile($env:ROLE_C_TTS_OUTPUT, $format)
    $synthesizer.Speak($env:ROLE_C_TTS_TEXT)
} finally {
    $synthesizer.Dispose()
}
