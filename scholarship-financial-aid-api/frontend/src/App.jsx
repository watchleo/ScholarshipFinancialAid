import { useCallback, useEffect, useMemo, useState } from "react";
import {
  IonApp,
  IonBadge,
  IonButton,
  IonButtons,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonCol,
  IonContent,
  IonGrid,
  IonHeader,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonMenu,
  IonMenuButton,
  IonMenuToggle,
  IonNote,
  IonPage,
  IonRefresher,
  IonRefresherContent,
  IonRow,
  IonSearchbar,
  IonSpinner,
  IonSplitPane,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import {
  peopleOutline,
  refreshOutline,
  schoolOutline,
  gridOutline,
  documentTextOutline,
} from "ionicons/icons";

const pages = [
  { id: "overview", label: "Overview", icon: gridOutline },
  { id: "students", label: "Students", icon: peopleOutline },
  { id: "scholarships", label: "Scholarships", icon: schoolOutline },
  { id: "applications", label: "Applications", icon: documentTextOutline },
];

const currency = new Intl.NumberFormat("en-PH", {
  style: "currency",
  currency: "PHP",
  maximumFractionDigits: 0,
});
const formatMoney = (value) => currency.format(Number(value) || 0);

async function getJSON(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body?.error?.message || `Request failed (${response.status})`);
  }
  return body;
}

function StatusBadge({ status }) {
  const color =
    status === "Approved" ? "success" : status === "Pending" ? "warning" : status === "Rejected" ? "danger" : "medium";
  return <IonBadge color={color}>{status || "Unknown"}</IonBadge>;
}

function DataTable({ columns, rows, emptyMessage }) {
  if (!rows.length) return <div className="empty-state">{emptyMessage}</div>;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  );
}

function ApplicationTable({ applications }) {
  return (
    <DataTable
      columns={["Application", "Student", "Program / aid", "Status", "Term", "Award"]}
      emptyMessage="No applications found."
      rows={applications.map((item) => (
        <tr key={item.Application_ID}>
          <td className="monospace">{item.Application_ID}</td>
          <td><strong>{item.Student_Name}</strong><IonNote className="subcell">{item.Student_ID}</IonNote></td>
          <td>{item.Scholarship_Name || item.Aid_Type || "Financial aid"}</td>
          <td><StatusBadge status={item.Status} /></td>
          <td>{item.Term_Name}<IonNote className="subcell">{item.Academic_Year}</IonNote></td>
          <td>{item.Award_Amount == null ? "—" : formatMoney(item.Award_Amount)}</td>
        </tr>
      ))}
    />
  );
}

function SectionHeading({ title, description, meta, children }) {
  return (
    <div className="section-heading">
      <div>
        <IonNote>{description}</IonNote>
        <h1>{title}</h1>
      </div>
      <div className="section-heading-actions">
        {meta && <IonNote>{meta}</IonNote>}
        {children}
      </div>
    </div>
  );
}

function App() {
  const [activePage, setActivePage] = useState("overview");
  const [students, setStudents] = useState([]);
  const [scholarships, setScholarships] = useState([]);
  const [applications, setApplications] = useState([]);
  const [summary, setSummary] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [studentSearch, setStudentSearch] = useState("");
  const [applicationSearch, setApplicationSearch] = useState("");
  const [updatedAt, setUpdatedAt] = useState("");

  const loadData = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const [nextSummary, studentResult, scholarshipResult, applicationResult] = await Promise.all([
        getJSON("/api/reports/summary"),
        getJSON("/api/students"),
        getJSON("/api/scholarships"),
        getJSON("/api/applications"),
      ]);
      setSummary(nextSummary);
      setStudents(studentResult.data || []);
      setScholarships(scholarshipResult.data || []);
      setApplications(applicationResult.data || []);
      setUpdatedAt(new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }));
      setApiOnline(true);
    } catch (requestError) {
      setApiOnline(false);
      setError(`${requestError.message}. Check that the API server is running, then refresh.`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredStudents = useMemo(() => {
    const query = studentSearch.trim().toLowerCase();
    return students.filter((student) =>
      `${student.Student_Name} ${student.Student_ID} ${student.Program} ${student.Email}`.toLowerCase().includes(query),
    );
  }, [students, studentSearch]);

  const filteredApplications = useMemo(() => {
    const query = applicationSearch.trim().toLowerCase();
    return applications.filter((application) =>
      `${application.Application_ID} ${application.Student_Name} ${application.Status} ${application.Scholarship_Name || ""} ${application.Aid_Type || ""}`
        .toLowerCase()
        .includes(query),
    );
  }, [applications, applicationSearch]);

  const pageTitle = pages.find((page) => page.id === activePage)?.label || "Overview";

  async function refresh(event) {
    await loadData();
    event.detail.complete();
  }

  return (
    <IonApp>
      <IonSplitPane contentId="main-content" when="lg">
        <IonMenu contentId="main-content" type="overlay">
          <IonHeader>
            <IonToolbar>
              <IonTitle>
                <span className="brand-mark">S</span>
                <span className="brand-title">Scholarship &amp; Aid</span>
              </IonTitle>
            </IonToolbar>
          </IonHeader>
          <IonContent>
            <IonList className="side-nav" lines="none">
              <IonNote className="nav-caption">WORKSPACE</IonNote>
              {pages.map((page) => (
                <IonMenuToggle key={page.id} autoHide={false}>
                  <IonItem
                    button
                    detail={false}
                    className={activePage === page.id ? "nav-item selected" : "nav-item"}
                    onClick={() => setActivePage(page.id)}
                  >
                    <IonIcon slot="start" icon={page.icon} />
                    <IonLabel>{page.label}</IonLabel>
                  </IonItem>
                </IonMenuToggle>
              ))}
            </IonList>
            <div className="menu-footer">
              <strong>Financial Aid Office</strong>
              Scholarship management
            </div>
          </IonContent>
        </IonMenu>

        <IonPage id="main-content">
          <IonHeader>
            <IonToolbar className="top-toolbar">
              <IonButtons slot="start">
                <IonMenuButton aria-label="Open navigation menu" />
              </IonButtons>
              <IonTitle>{pageTitle}</IonTitle>
              <div slot="end" className="toolbar-actions">
                <span className={`api-state ${apiOnline ? "online" : "offline"}`}>
                  <span className="api-dot" />
                  {loading && !updatedAt ? "Connecting" : apiOnline ? "API connected" : "API unavailable"}
                </span>
                <IonButton fill="clear" aria-label="Refresh data" onClick={loadData}>
                  <IonIcon slot="icon-only" icon={refreshOutline} />
                </IonButton>
              </div>
            </IonToolbar>
          </IonHeader>

          <IonContent className="main-content">
            <IonRefresher slot="fixed" onIonRefresh={refresh}>
              <IonRefresherContent />
            </IonRefresher>
            <main>
              {error && <div className="error-banner" role="alert">{error}</div>}
              {loading && !summary ? (
                <div className="loading-state"><IonSpinner name="crescent" /><IonNote>Loading dashboard data…</IonNote></div>
              ) : (
                <>
                  {activePage === "overview" && (
                    <>
                      <SectionHeading
                        title="Overview"
                        description="Scholarship office"
                        meta={updatedAt ? `Updated ${updatedAt}` : ""}
                      />
                      <IonGrid className="metrics-grid">
                        <IonRow>
                          <Metric label="Records in system" value={summary?.total_records ?? "—"} note="Across all data tables" />
                          <Metric label="Pending applications" value={summary?.pending ?? 0} note="Awaiting review" />
                          <Metric label="Approved applications" value={summary?.approved ?? 0} note="Current records" />
                          <Metric label="Total awarded" value={formatMoney(summary?.total_awarded)} note={`Disbursed ${formatMoney(summary?.total_disbursed)}`} />
                        </IonRow>
                      </IonGrid>
                      <div className="content-section">
                        <div className="section-title-row">
                          <div><h2>Recent applications</h2><IonNote>{applications.length} applications on file</IonNote></div>
                          <IonButton fill="clear" onClick={() => setActivePage("applications")}>View applications</IonButton>
                        </div>
                        <ApplicationTable applications={[...applications].reverse().slice(0, 5)} />
                      </div>
                    </>
                  )}
                  {activePage === "students" && (
                    <>
                      <SectionHeading title="Students" description="People" />
                      <div className="content-section">
                        <div className="section-title-row">
                          <div><h2>Student directory</h2><IonNote>{filteredStudents.length} of {students.length} students</IonNote></div>
                          <IonSearchbar
                            className="table-search"
                            value={studentSearch}
                            onIonInput={(event) => setStudentSearch(event.detail.value || "")}
                            placeholder="Search name or program"
                            aria-label="Search students"
                          />
                        </div>
                        <DataTable
                          columns={["Student", "Program", "Year", "GPA", "Household income", "Email"]}
                          emptyMessage="No matching students."
                          rows={filteredStudents.map((student) => (
                            <tr key={student.Student_ID}>
                              <td><strong>{student.Student_Name}</strong><IonNote className="subcell monospace">{student.Student_ID}</IonNote></td>
                              <td>{student.Program}</td><td>{student.Year_Level}</td>
                              <td>{student.GPA}</td><td>{formatMoney(student.Household_Income)}</td>
                              <td>{student.Email}</td>
                            </tr>
                          ))}
                        />
                      </div>
                    </>
                  )}
                  {activePage === "scholarships" && (
                    <>
                      <SectionHeading title="Scholarships" description="Programs" />
                      <div className="content-section">
                        <div className="section-title-row">
                          <div><h2>Scholarship programs</h2><IonNote>{scholarships.length} programs</IonNote></div>
                        </div>
                        <DataTable
                          columns={["Program", "Type", "Slots", "Maximum GPA", "Income limit"]}
                          emptyMessage="No scholarship programs found."
                          rows={scholarships.map((item) => (
                            <tr key={item.Scholarship_ID}>
                              <td><strong>{item.Scholarship_Name}</strong><IonNote className="subcell monospace">{item.Scholarship_ID}</IonNote></td>
                              <td>{item.Scholarship_Type}</td><td>{item.Scholarship_Slots}</td>
                              <td>{item.Max_GPA_Allowed}</td><td>{formatMoney(item.Max_Household_Income)}</td>
                            </tr>
                          ))}
                        />
                      </div>
                    </>
                  )}
                  {activePage === "applications" && (
                    <>
                      <SectionHeading title="Applications" description="Case management" />
                      <div className="content-section">
                        <div className="section-title-row">
                          <div><h2>All applications</h2><IonNote>{filteredApplications.length} of {applications.length} applications</IonNote></div>
                          <IonSearchbar
                            className="table-search"
                            value={applicationSearch}
                            onIonInput={(event) => setApplicationSearch(event.detail.value || "")}
                            placeholder="Search student or status"
                            aria-label="Search applications"
                          />
                        </div>
                        <ApplicationTable applications={filteredApplications} />
                      </div>
                    </>
                  )}
                </>
              )}
            </main>
          </IonContent>
        </IonPage>
      </IonSplitPane>
    </IonApp>
  );
}

function Metric({ label, value, note }) {
  return (
    <IonCol size="12" sizeSm="6" sizeXl="3">
      <IonCard className="metric-card">
        <IonCardHeader>
          <IonCardTitle>{label}</IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          <strong className="metric-value">{value}</strong>
          <IonNote>{note}</IonNote>
        </IonCardContent>
      </IonCard>
    </IonCol>
  );
}

export default App;
