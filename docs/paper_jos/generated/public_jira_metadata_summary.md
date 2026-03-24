# The Public Jira Dataset Metadata Summary

这份总表把 TPJD 官方分散的 metadata 与本地恢复后的 collection 统计合并到了一处。

## 1. Source Overview

| source_name   |   restored_issue_count |   project_count |   documented_field_count |   custom_field_count | min_created                  | max_created                  | selected_for_paper_sample   | selected_projects             |
|:--------------|-----------------------:|----------------:|-------------------------:|---------------------:|:-----------------------------|:-----------------------------|:----------------------------|:------------------------------|
| Apache        |                1014926 |             646 |                      211 |                  171 | 0010-04-03T23:04:00.000+0000 | 2022-01-05T23:07:48.000+0000 | True                        | Spark                         |
| Mojang        |                 420819 |               8 |                       65 |                   37 | 2012-09-06T15:16:10.000+0300 | 2022-01-05T08:00:38.000+0200 | False                       |                               |
| RedHat        |                 353000 |             241 |                      270 |                  228 | 2001-04-06T03:49:30.000+0000 | 2022-01-04T20:53:48.000+0000 | True                        | Keycloak                      |
| Jira          |                 274545 |              30 |                      218 |                  176 | 1982-11-26T02:23:00.000+0000 | 2022-01-05T14:37:58.000+0000 | True                        | Jira Server and Data Center   |
| Qt            |                 148579 |              21 |                       76 |                   36 | 2003-09-23T11:25:00.000+0000 | 2022-01-04T15:32:16.000+0000 | True                        | Qt                            |
| MongoDB       |                 137172 |              27 |                      220 |                  190 | 2009-04-08T08:01:26.000+0000 | 2022-01-04T16:08:10.000+0000 | True                        | Core Server                   |
| Sonatype      |                  87284 |               5 |                      102 |                   62 | 2008-04-03T14:47:48.000+0000 | 2022-01-04T12:19:07.000+0000 | False                       |                               |
| Spring        |                  69156 |              80 |                       68 |                   28 | 2003-11-26T08:35:42.000+0000 | 2021-12-22T17:42:16.000+0000 | False                       |                               |
| Sakai         |                  50550 |              53 |                      160 |                  117 | 2004-09-24T07:16:11.000-0400 | 2022-01-05T20:17:21.429-0500 | False                       |                               |
| JiraEcosystem |                  41866 |             101 |                      516 |                  472 | 2004-11-16T23:29:40.412-0600 | 2022-01-04T01:44:25.564-0600 | False                       |                               |
| MariaDB       |                  31229 |              11 |                        0 |                    0 | 2009-02-17T16:48:26.000+0000 | 2021-01-26T12:55:41.000+0000 | False                       |                               |
| Hyperledger   |                  28146 |              32 |                       81 |                   41 | 2016-07-18T17:01:57.000+0000 | 2021-12-27T13:40:20.000+0000 | False                       |                               |
| JFrog         |                  15535 |              10 |                      178 |                  138 | 2006-10-04T12:19:24.000+0000 | 2022-01-04T06:21:48.000+0000 | True                        | Artifactory Binary Repository |
| IntelDAOS     |                   9474 |               2 |                       79 |                   37 | 2015-07-20T18:29:51.000-0700 | 2022-01-03T10:36:54.143-0800 | False                       |                               |
| Mindville     |                   2134 |               7 |                        0 |                    0 | 2015-08-13T15:21:00.000+0000 | 2021-04-22T23:17:42.000+0000 | False                       |                               |
| SecondLife    |                   1867 |               2 |                      163 |                  124 | 2007-01-18T01:44:43.000-0600 | 2021-11-13T08:57:54.000-0600 | False                       |                               |

## 2. Paper Sample

| collection   | project                       |   exported_count | min_created                  | max_created                  |
|:-------------|:------------------------------|-----------------:|:-----------------------------|:-----------------------------|
| Apache       | Spark                         |              500 | 2021-11-14T06:02:55.000+0000 | 2022-01-05T11:37:21.000+0000 |
| JFrog        | Artifactory Binary Repository |              500 | 2021-07-20T05:57:29.000+0000 | 2022-01-04T06:21:48.000+0000 |
| Jira         | Jira Server and Data Center   |              500 | 2021-07-12T18:11:19.000+0000 | 2022-01-04T20:45:19.000+0000 |
| MongoDB      | Core Server                   |              500 | 2021-12-01T13:40:08.000+0000 | 2022-01-04T13:59:54.000+0000 |
| Qt           | Qt                            |              500 | 2021-12-07T13:13:48.000+0000 | 2022-01-04T14:52:39.000+0000 |
| RedHat       | Keycloak                      |              500 | 2021-09-01T10:17:32.000+0000 | 2021-12-30T03:10:58.000+0000 |

## 3. Normalized Dataset Summary

| metric                 | value                                                                                                                                                                                                           |
|:-----------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| dataset_label          | The Public Jira Dataset                                                                                                                                                                                         |
| row_count_final        | 3000                                                                                                                                                                                                            |
| column_count           | 12                                                                                                                                                                                                              |
| created_at_min         | 2021-07-12T18:11:19Z                                                                                                                                                                                            |
| created_at_max         | 2022-01-05T11:37:21Z                                                                                                                                                                                            |
| reporter_unique        | 1288                                                                                                                                                                                                            |
| assignee_unique        | 321                                                                                                                                                                                                             |
| comments_count_mean    | 1.13                                                                                                                                                                                                            |
| comments_count_median  | 0.0                                                                                                                                                                                                             |
| severity_source_counts | {"priority_fallback": 2724, "issuetype_fallback": 276}                                                                                                                                                          |
| project_counts         | {"Artifactory Binary Repository": 500, "Core Server": 500, "Jira Server and Data Center": 500, "Keycloak": 500, "Qt": 500, "Spark": 500}                                                                        |
| missing_counts         | {"title": 0, "description": 0, "severity": 0, "component": 859, "product/project": 0, "created_at": 0, "resolved_at": 2012, "reporter": 0, "assignee": 1539, "status": 0, "priority": 276, "comments_count": 0} |
