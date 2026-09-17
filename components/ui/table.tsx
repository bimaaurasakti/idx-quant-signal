import * as React from "react";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

import { cn } from "@/lib/utils";

function Table({ className, ...props }: React.ComponentProps<"table">) {
  return (
    <div data-slot="table-container" className="relative w-full overflow-x-auto">
      <table
        data-slot="table"
        className={cn("w-full caption-bottom text-xs", className)}
        {...props}
      />
    </div>
  );
}

function TableHeader({ className, ...props }: React.ComponentProps<"thead">) {
  return (
    <thead
      data-slot="table-header"
      className={cn("sticky top-0 z-10 border-b border-border bg-surface-1/95 backdrop-blur-xs text-text-secondary", className)}
      {...props}
    />
  );
}

function TableBody({ className, ...props }: React.ComponentProps<"tbody">) {
  return (
    <tbody
      data-slot="table-body"
      className={cn("[&_tr:last-child]:border-0 divide-y divide-border/60", className)}
      {...props}
    />
  );
}

function TableFooter({ className, ...props }: React.ComponentProps<"tfoot">) {
  return (
    <tfoot
      data-slot="table-footer"
      className={cn("border-t border-border bg-surface-1 font-medium text-text-primary", className)}
      {...props}
    />
  );
}

function TableRow({ className, ...props }: React.ComponentProps<"tr">) {
  return (
    <tr
      data-slot="table-row"
      className={cn(
        "border-b border-border/50 transition-colors duration-100 hover:bg-surface-2/50 data-[state=selected]:bg-surface-2",
        className,
      )}
      {...props}
    />
  );
}

function TableHead({ className, ...props }: React.ComponentProps<"th">) {
  return (
    <th
      data-slot="table-head"
      className={cn(
        "h-9 px-3 py-2 text-left align-middle font-medium text-text-secondary whitespace-nowrap [&:has([role=checkbox])]:pr-0",
        className,
      )}
      {...props}
    />
  );
}

function TableCell({ className, ...props }: React.ComponentProps<"td">) {
  return (
    <td
      data-slot="table-cell"
      className={cn("px-3 py-2.5 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0", className)}
      {...props}
    />
  );
}

function TableCaption({ className, ...props }: React.ComponentProps<"caption">) {
  return (
    <caption
      data-slot="table-caption"
      className={cn("mt-4 text-xs text-text-muted", className)}
      {...props}
    />
  );
}

interface TableSortHeadProps extends React.ComponentProps<"th"> {
  isSorted?: boolean;
  sortDirection?: "asc" | "desc";
  onSort?: () => void;
  children: React.ReactNode;
}

function TableSortHead({
  isSorted = false,
  sortDirection = "desc",
  onSort,
  className,
  children,
  ...props
}: TableSortHeadProps) {
  return (
    <th
      data-slot="table-sort-head"
      onClick={onSort}
      className={cn(
        "h-9 px-3 py-2 text-left align-middle font-medium text-text-secondary whitespace-nowrap select-none",
        onSort && "cursor-pointer hover:text-text-primary transition-colors duration-100",
        isSorted && "text-text-primary font-semibold",
        className,
      )}
      {...props}
    >
      <div className={cn("inline-flex items-center gap-1", className?.includes("text-right") && "justify-end w-full")}>
        <span>{children}</span>
        {onSort && (
          <span className="text-text-muted">
            {isSorted ? (
              sortDirection === "asc" ? (
                <ArrowUp className="size-3 text-brand" />
              ) : (
                <ArrowDown className="size-3 text-brand" />
              )
            ) : (
              <ArrowUpDown className="size-3 opacity-40 hover:opacity-100 transition-opacity" />
            )}
          </span>
        )}
      </div>
    </th>
  );
}

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
  TableSortHead,
};
