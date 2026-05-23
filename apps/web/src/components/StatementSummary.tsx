import { ArrowDownLeft, ArrowUpRight, Download, ReceiptText, Scale, Search, X } from "lucide-react";

import type { Direction, StatementParseResponse, Transaction } from "../api/types";

type StatementSummaryProps = {
  statement: StatementParseResponse;
  filteredTransactions: Transaction[];
  search: string;
  direction: "ALL" | Direction;
  selectedTransaction: Transaction | null;
  onSearchChange: (value: string) => void;
  onDirectionChange: (value: "ALL" | Direction) => void;
  onExport: (format: "tsv" | "csv") => void;
  onSelectTransaction: (transaction: Transaction) => void;
  onCloseDetail: () => void;
};

export function StatementSummary({
  statement,
  filteredTransactions,
  search,
  direction,
  selectedTransaction,
  onSearchChange,
  onDirectionChange,
  onExport,
  onSelectTransaction,
  onCloseDetail,
}: StatementSummaryProps) {
  return (
    <section className="statement-view">
      <header className="statement-header">
        <div>
          <h2>{displayName(statement.parser_name)}</h2>
          <p>
            Statement date: {statement.statement_date} <span>Period: {statement.period}</span>
          </p>
        </div>
        <span className="count-pill">
          <ReceiptText aria-hidden="true" size={15} />
          {statement.transaction_count} rows
        </span>
      </header>

      <div className="totals-strip">
        <Metric label="Debit" value={statement.totals.debit} tone="debit" />
        <Metric label="Credit" value={statement.totals.credit} tone="credit" />
        <Metric label="Net" value={statement.totals.net} tone="net" />
      </div>

      <div className="transaction-toolbar">
        <label className="search-field">
          <Search aria-hidden="true" size={16} />
          <input
            value={search}
            placeholder="Search transactions"
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </label>
        <select
          value={direction}
          onChange={(event) => onDirectionChange(event.target.value as "ALL" | Direction)}
        >
          <option value="ALL">All directions</option>
          <option value="DEBIT">Debit</option>
          <option value="CREDIT">Credit</option>
        </select>
        <button className="icon-action" onClick={() => onExport("tsv")} title="Export TSV">
          <Download size={16} />
          TSV
        </button>
        <button className="icon-action" onClick={() => onExport("csv")} title="Export CSV">
          <Download size={16} />
          CSV
        </button>
      </div>

      <TransactionTable
        transactions={filteredTransactions}
        onSelectTransaction={onSelectTransaction}
      />
      <TransactionCards
        transactions={filteredTransactions}
        onSelectTransaction={onSelectTransaction}
      />

      <footer className="table-footer">{filteredTransactions.length} rows shown</footer>

      {selectedTransaction ? (
        <TransactionDetail transaction={selectedTransaction} onClose={onCloseDetail} />
      ) : null}
    </section>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "debit" | "credit" | "net" }) {
  const Icon = tone === "debit" ? ArrowUpRight : tone === "credit" ? ArrowDownLeft : Scale;

  return (
    <div className={`metric ${tone}`}>
      <span>
        <Icon aria-hidden="true" size={16} />
        {label}
      </span>
      <strong>{formatMoney(value)}</strong>
    </div>
  );
}

function TransactionTable({
  transactions,
  onSelectTransaction,
}: {
  transactions: Transaction[];
  onSelectTransaction: (transaction: Transaction) => void;
}) {
  return (
    <div className="table-wrap">
      <table>
        <colgroup>
          <col className="date-column" />
          <col className="date-column" />
          <col className="description-column" />
          <col className="amount-column" />
          <col className="direction-column" />
          <col className="card-column" />
          <col className="cardholder-column" />
          <col className="source-column" />
        </colgroup>
        <thead>
          <tr>
            <th>Txn Date</th>
            <th>Post Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Direction</th>
            <th>Card</th>
            <th>Cardholder</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction, index) => (
            <tr
              key={`${transaction.txn_date}-${transaction.description}-${index}`}
              onClick={() => onSelectTransaction(transaction)}
            >
              <td className="date-cell">
                <time dateTime={transaction.txn_date}>{formatDate(transaction.txn_date)}</time>
              </td>
              <td className="date-cell">
                <time dateTime={transaction.post_date}>{formatDate(transaction.post_date)}</time>
              </td>
              <td className="description-cell">
                {transaction.description}
              </td>
              <td className="amount-cell">{formatMoney(transaction.amount)}</td>
              <td>
                <span className={`direction ${transaction.direction.toLowerCase()}`}>
                  {transaction.direction}
                </span>
              </td>
              <td className="card-cell">{transaction.card_last4}</td>
              <td className="cardholder-cell">{transaction.cardholder}</td>
              <td className="source-cell" title={transaction.source_file}>
                {transaction.source_file}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TransactionCards({
  transactions,
  onSelectTransaction,
}: {
  transactions: Transaction[];
  onSelectTransaction: (transaction: Transaction) => void;
}) {
  return (
    <div className="transaction-cards">
      {transactions.map((transaction, index) => (
        <button
          key={`${transaction.txn_date}-${transaction.description}-${index}`}
          className="transaction-card"
          onClick={() => onSelectTransaction(transaction)}
        >
          <span>
            {transaction.txn_date}
            <strong className={`direction ${transaction.direction.toLowerCase()}`}>
              {transaction.direction}
            </strong>
          </span>
          <strong>{transaction.description}</strong>
          <em>{formatMoney(transaction.amount)} IDR</em>
        </button>
      ))}
    </div>
  );
}

function TransactionDetail({
  transaction,
  onClose,
}: {
  transaction: Transaction;
  onClose: () => void;
}) {
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="detail-drawer" onClick={(event) => event.stopPropagation()}>
        <header>
          <h3>Transaction Detail</h3>
          <button onClick={onClose} aria-label="Close detail">
            <X size={18} />
          </button>
        </header>
        <dl>
          <dt>Description</dt>
          <dd>{transaction.description}</dd>
          <dt>Amount</dt>
          <dd>{formatMoney(transaction.amount)} IDR</dd>
          <dt>Direction</dt>
          <dd>{transaction.direction}</dd>
          <dt>Txn Date</dt>
          <dd>{transaction.txn_date}</dd>
          <dt>Post Date</dt>
          <dd>{transaction.post_date}</dd>
          <dt>Card</dt>
          <dd>{transaction.card_last4}</dd>
          <dt>Cardholder</dt>
          <dd>{transaction.cardholder}</dd>
          <dt>Source</dt>
          <dd>{transaction.source_file}</dd>
        </dl>
      </aside>
    </div>
  );
}

function displayName(parserName: string) {
  if (parserName === "cimb_cc") {
    return "CIMB Niaga Sharia Credit Card";
  }
  return parserName.replaceAll("_", " ");
}

function formatMoney(value: string) {
  const n = Number(value);
  if (!Number.isFinite(n)) {
    return value;
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(n);
}

function formatDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(Date.UTC(year, month - 1, day)));
}
