import { useEffect, useMemo, useState } from "react";
import { FileText } from "lucide-react";

import { fetchParsers, parseStatement } from "./api/client";
import type {
  ApiError,
  Direction,
  ParserMetadata,
  StatementParseResponse,
  Transaction,
} from "./api/types";
import { AppShell } from "./components/AppShell";
import { ParseError } from "./components/ParseError";
import { StatementSummary } from "./components/StatementSummary";
import { StatementUploadPanel } from "./components/StatementUploadPanel";

type DirectionFilter = "ALL" | Direction;

export default function App() {
  const [parsers, setParsers] = useState<ParserMetadata[]>([]);
  const [parserLoadError, setParserLoadError] = useState<string | null>(null);
  const [selectedParser, setSelectedParser] = useState("");
  const [password, setPassword] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [statement, setStatement] = useState<StatementParseResponse | null>(null);
  const [parseError, setParseError] = useState<ApiError | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [search, setSearch] = useState("");
  const [direction, setDirection] = useState<DirectionFilter>("ALL");
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);

  useEffect(() => {
    fetchParsers()
      .then((nextParsers) => {
        setParsers(nextParsers);
        setParserLoadError(null);
      })
      .catch((error: ApiError) => {
        setParserLoadError(error.message ?? "Could not load parsers.");
      });
  }, []);

  const filteredTransactions = useMemo(() => {
    if (!statement) {
      return [];
    }
    const normalizedSearch = search.trim().toLowerCase();
    return statement.transactions.filter((transaction) => {
      const matchesDirection = direction === "ALL" || transaction.direction === direction;
      const matchesSearch =
        normalizedSearch.length === 0 ||
        transaction.description.toLowerCase().includes(normalizedSearch) ||
        transaction.cardholder.toLowerCase().includes(normalizedSearch) ||
        transaction.card_last4.includes(normalizedSearch);
      return matchesDirection && matchesSearch;
    });
  }, [direction, search, statement]);

  async function handleParse() {
    if (!file) {
      return;
    }
    setIsParsing(true);
    setParseError(null);
    setSelectedTransaction(null);
    try {
      const parsed = await parseStatement({
        file,
        password,
        parserName: selectedParser,
      });
      setStatement(parsed);
      setSearch("");
      setDirection("ALL");
    } catch (error) {
      const apiError = error as ApiError;
      setParseError({
        error: apiError.error ?? "REQUEST_FAILED",
        message: apiError.message ?? "The statement could not be parsed.",
      });
    } finally {
      setIsParsing(false);
    }
  }

  function handleExport(format: "tsv" | "csv") {
    if (!statement) {
      return;
    }
    const delimiter = format === "tsv" ? "\t" : ",";
    const rows = [
      [
        "statement_period",
        "txn_date",
        "post_date",
        "description",
        "amount",
        "direction",
        "card_last4",
        "cardholder",
        "source_file",
      ],
      ...filteredTransactions.map((transaction) => [
        statement.period,
        transaction.txn_date,
        transaction.post_date,
        transaction.description,
        transaction.amount.toFixed(2),
        transaction.direction,
        transaction.card_last4,
        transaction.cardholder,
        transaction.source_file,
      ]),
    ];
    const content = rows.map((row) => row.map((cell) => escapeCell(cell, delimiter)).join(delimiter)).join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${statement.period}_${statement.bank_label}.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AppShell parserCount={parsers.length}>
      <StatementUploadPanel
        parsers={parsers}
        selectedParser={selectedParser}
        password={password}
        file={file}
        isParsing={isParsing}
        parserLoadError={parserLoadError}
        onParserChange={setSelectedParser}
        onPasswordChange={setPassword}
        onFileChange={setFile}
        onParse={handleParse}
      />

      <section className="result-panel">
        {isParsing ? (
          <ParsingState fileName={file?.name ?? "statement.pdf"} />
        ) : parseError ? (
          <ParseError error={parseError} onRetry={handleParse} />
        ) : statement ? (
          <StatementSummary
            statement={statement}
            filteredTransactions={filteredTransactions}
            search={search}
            direction={direction}
            selectedTransaction={selectedTransaction}
            onSearchChange={setSearch}
            onDirectionChange={setDirection}
            onExport={handleExport}
            onSelectTransaction={setSelectedTransaction}
            onCloseDetail={() => setSelectedTransaction(null)}
          />
        ) : (
          <EmptyState parserLabel={parsers[0]?.display_name ?? "CIMB Niaga Sharia Credit Card"} />
        )}
      </section>
    </AppShell>
  );
}

function EmptyState({ parserLabel }: { parserLabel: string }) {
  return (
    <section className="state-panel empty-state">
      <FileText aria-hidden="true" size={30} />
      <div>
        <h2>Statement Workspace</h2>
        <p>Drop a PDF statement on the left to inspect parsed transactions here.</p>
        <span>Supported now: {parserLabel}</span>
      </div>
    </section>
  );
}

function ParsingState({ fileName }: { fileName: string }) {
  const steps = [
    ["Upload received", "done"],
    ["Decrypting PDF", "done"],
    ["Detecting parser", "active"],
    ["Extracting transactions", "pending"],
    ["Preparing result", "pending"],
  ] as const;

  return (
    <section className="state-panel parsing-state">
      <FileText aria-hidden="true" size={30} />
      <div>
        <h2>Parsing Statement</h2>
        <strong>{fileName}</strong>
        <ol>
          {steps.map(([label, state], index) => (
            <li key={label} className={state}>
              <span>Step {index + 1}</span>
              {label}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function escapeCell(value: string | number, delimiter: string) {
  const text = String(value);
  if (text.includes(delimiter) || text.includes("\n") || text.includes('"')) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}
