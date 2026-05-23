import { FileUp, Lock, Play, ShieldCheck, Upload } from "lucide-react";

import type { ParserMetadata } from "../api/types";

type StatementUploadPanelProps = {
  parsers: ParserMetadata[];
  selectedParser: string;
  password: string;
  file: File | null;
  isParsing: boolean;
  parserLoadError: string | null;
  onParserChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onFileChange: (file: File | null) => void;
  onParse: () => void;
};

export function StatementUploadPanel({
  parsers,
  selectedParser,
  password,
  file,
  isParsing,
  parserLoadError,
  onParserChange,
  onPasswordChange,
  onFileChange,
  onParse,
}: StatementUploadPanelProps) {
  const canParse = Boolean(file) && !isParsing;

  return (
    <aside className="upload-panel">
      <section>
        <h2>Upload Statement</h2>
        <label className="field">
          <span>Bank / Parser</span>
          <select
            value={selectedParser}
            onChange={(event) => onParserChange(event.target.value)}
          >
            <option value="">Auto-detect</option>
            {parsers.map((parser) => (
              <option key={parser.name} value={parser.name}>
                {parser.display_name}
              </option>
            ))}
          </select>
        </label>
        {parserLoadError ? <p className="inline-error">{parserLoadError}</p> : null}

        <label className="field">
          <span>PDF Password</span>
          <div className="input-with-icon">
            <Lock aria-hidden="true" size={16} />
            <input
              type="password"
              placeholder="Optional"
              value={password}
              onChange={(event) => onPasswordChange(event.target.value)}
            />
          </div>
        </label>

        <label
          className="dropzone"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            onFileChange(event.dataTransfer.files[0] ?? null);
          }}
        >
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          />
          <Upload aria-hidden="true" size={24} />
          <strong>{file ? file.name : "Drop PDF here"}</strong>
          <span>{file ? "Selected PDF" : "or choose file"}</span>
        </label>

        <button className="primary-action" disabled={!canParse} onClick={onParse}>
          {isParsing ? <FileUp size={18} /> : <Play size={18} />}
          {isParsing ? "Parsing..." : "Parse Statement"}
        </button>
      </section>

      <section className="support-block">
        <h3>Privacy</h3>
        <label className="radio-row">
          <input type="radio" checked readOnly />
          <span>Do not save PDF</span>
        </label>
        <label className="radio-row disabled">
          <input type="radio" disabled />
          <span>Save locally</span>
        </label>
      </section>

      <section className="support-block">
        <h3>Supported Formats</h3>
        {parsers.length ? (
          <ul>
            {parsers.map((parser) => (
              <li key={parser.name}>
                <ShieldCheck size={15} />
                <span>{parser.display_name}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>No parser metadata loaded.</p>
        )}
      </section>
    </aside>
  );
}
